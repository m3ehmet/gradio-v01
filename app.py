import gradio as gr
import openai
import PyPDF2
import docx
import json
from datetime import datetime
import os

# ============================================
# DOSYA OKUMA FONKSİYONLARI
# ============================================

def extract_text_from_file(file_path):
    """Dosyadan metin çıkarma"""
    text = ""
    
    try:
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        
        else:  # txt
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
    
    except Exception as e:
        return f"Hata: {str(e)}"
    
    return text

# ============================================
# ANALİZ FONKSİYONLARI
# ============================================

def analyze_contract(file, api_key):
    """Sözleşmeyi analiz et"""
    
    if not api_key:
        return "❌ **Hata:** OpenAI API key girin!", None, None
    
    if file is None:
        return "❌ **Hata:** Dosya yükleyin!", None, None
    
    openai.api_key = api_key
    
    # Dosyayı oku
    contract_text = extract_text_from_file(file)
    
    if contract_text.startswith("Hata:"):
        return f"❌ **{contract_text}**", None, None
    
    if len(contract_text) < 50:
        return "❌ **Hata:** Dosya boş veya okunamadı!", None, None
    
    # Prompt oluştur
    prompt = f"""
Sen deneyimli bir hukuk danışmanısın. Aşağıdaki sözleşmeyi detaylı analiz et.

Sözleşme Metni:
\"\"\"
{contract_text[:15000]}
\"\"\"

Bu sözleşmeyi analiz et ve şu JSON formatında yanıt ver:

{{
  "contract_type": "Sözleşme türü (örn: İş sözleşmesi, Hizmet sözleşmesi, vb.)",
  "parties": {{
    "party_a": "Taraf 1 adı veya 'Belirtilmemiş'",
    "party_b": "Taraf 2 adı veya 'Belirtilmemiş'"
  }},
  "key_dates": [
    {{"date": "tarih", "description": "açıklama"}},
    {{"date": "tarih", "description": "açıklama"}}
  ],
  "financial_terms": [
    {{"term": "terim", "amount": "tutar", "description": "açıklama"}},
    {{"term": "terim", "amount": "tutar", "description": "açıklama"}}
  ],
  "critical_points": [
    {{
      "category": "Kategori (örn: Ödeme, Fesih, Sorumluluk, vb.)",
      "point": "Kritik nokta açıklaması",
      "risk_level": "Yüksek/Orta/Düşük",
      "recommendation": "Öneri"
    }},
    {{
      "category": "Kategori",
      "point": "Kritik nokta açıklaması",
      "risk_level": "Yüksek/Orta/Düşük",
      "recommendation": "Öneri"
    }}
  ],
  "obligations": {{
    "party_a": ["yükümlülük 1", "yükümlülük 2"],
    "party_b": ["yükümlülük 1", "yükümlülük 2"]
  }},
  "termination_clauses": [
    "Fesih maddesi 1",
    "Fesih maddesi 2"
  ],
  "risks": [
    {{
      "risk": "Risk açıklaması",
      "severity": "Yüksek/Orta/Düşük",
      "mitigation": "Azaltma önerisi"
    }},
    {{
      "risk": "Risk açıklaması",
      "severity": "Yüksek/Orta/Düşük",
      "mitigation": "Azaltma önerisi"
    }}
  ],
  "missing_clauses": [
    "Eksik madde 1",
    "Eksik madde 2"
  ],
  "overall_assessment": "Genel değerlendirme (2-3 cümle)"
}}

Türkçe yanıt ver. Detaylı ve kapsamlı ol. Yanıtını SADECE JSON formatında ver.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen deneyimli bir hukuk danışmanısın. Sözleşmeleri detaylı analiz eder ve kritik noktaları belirlersin. Yanıtlarını her zaman JSON formatında verirsin."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Sonucu formatla
        output = format_analysis_result(result)
        
        return output, result, contract_text
    
    except json.JSONDecodeError:
        return "❌ **Hata:** AI yanıtı JSON formatında değil. Lütfen tekrar deneyin.", None, None
    except Exception as e:
        return f"❌ **Hata:** {str(e)}", None, None

def format_analysis_result(result):
    """Analiz sonucunu formatla"""
    
    output = f"""
# 📄 {result.get('contract_type', 'Sözleşme')}

## 📝 Genel Değerlendirme
{result.get('overall_assessment', '-')}

---

## 👥 Taraflar
- **Taraf 1:** {result.get('parties', {}).get('party_a', '-')}
- **Taraf 2:** {result.get('parties', {}).get('party_b', '-')}

---

## 📅 Önemli Tarihler
"""
    
    if result.get('key_dates'):
        for date in result['key_dates']:
            output += f"- **{date.get('date', '-')}:** {date.get('description', '-')}\n"
    else:
        output += "- Tarih belirtilmemiş\n"
    
    output += "\n---\n\n## 💰 Finansal Şartlar\n"
    
    if result.get('financial_terms'):
        for term in result['financial_terms']:
            output += f"- **{term.get('term', '-')}:** {term.get('amount', '-')}\n"
            output += f"  - {term.get('description', '-')}\n"
    else:
        output += "- Finansal şart belirtilmemiş\n"
    
    output += "\n---\n\n## 🔴 Kritik Noktalar\n"
    
    if result.get('critical_points'):
        high_risk = [p for p in result['critical_points'] if p.get('risk_level') == 'Yüksek']
        medium_risk = [p for p in result['critical_points'] if p.get('risk_level') == 'Orta']
        low_risk = [p for p in result['critical_points'] if p.get('risk_level') == 'Düşük']
        
        if high_risk:
            output += "\n### 🔴 Yüksek Risk\n"
            for point in high_risk:
                output += f"- **{point.get('category', '-')}:** {point.get('point', '-')}\n"
                output += f"  - 💡 Öneri: {point.get('recommendation', '-')}\n"
        
        if medium_risk:
            output += "\n### 🟡 Orta Risk\n"
            for point in medium_risk:
                output += f"- **{point.get('category', '-')}:** {point.get('point', '-')}\n"
                output += f"  - 💡 Öneri: {point.get('recommendation', '-')}\n"
        
        if low_risk:
            output += "\n### 🟢 Düşük Risk\n"
            for point in low_risk:
                output += f"- **{point.get('category', '-')}:** {point.get('point', '-')}\n"
                output += f"  - 💡 Öneri: {point.get('recommendation', '-')}\n"
    else:
        output += "- Kritik nokta bulunamadı\n"
    
    output += "\n---\n\n## ⚠️ Tespit Edilen Riskler\n"
    
    if result.get('risks'):
        for risk in result['risks']:
            severity = risk.get('severity', 'Orta')
            icon = "🔴" if severity == "Yüksek" else "🟡" if severity == "Orta" else "🟢"
            output += f"{icon} **{risk.get('risk', '-')}** (Seviye: {severity})\n"
            output += f"   - Azaltma: {risk.get('mitigation', '-')}\n"
    else:
        output += "✅ Önemli risk tespit edilmedi\n"
    
    output += "\n---\n\n## 📋 Taraf Yükümlülükleri\n"
    
    if result.get('obligations'):
        output += f"\n### {result.get('parties', {}).get('party_a', 'Taraf 1')} Yükümlülükleri\n"
        for obligation in result['obligations'].get('party_a', []):
            output += f"- {obligation}\n"
        
        output += f"\n### {result.get('parties', {}).get('party_b', 'Taraf 2')} Yükümlülükleri\n"
        for obligation in result['obligations'].get('party_b', []):
            output += f"- {obligation}\n"
    
    output += "\n---\n\n## 🚪 Fesih Maddeleri\n"
    
    if result.get('termination_clauses'):
        for clause in result['termination_clauses']:
            output += f"- {clause}\n"
    else:
        output += "⚠️ Fesih maddesi bulunamadı!\n"
    
    output += "\n---\n\n## ⚠️ Eksik Olabilecek Maddeler\n"
    
    if result.get('missing_clauses'):
        for clause in result['missing_clauses']:
            output += f"- {clause}\n"
    else:
        output += "✅ Önemli eksik madde tespit edilmedi\n"
    
    return output

def ask_question(question, contract_text, api_key):
    """Sözleşme hakkında soru sor"""
    
    if not question:
        return "❌ Lütfen bir soru yazın!"
    
    if not contract_text:
        return "❌ Önce sözleşmeyi analiz edin!"
    
    if not api_key:
        return "❌ API key girin!"
    
    openai.api_key = api_key
    
    prompt = f"""
Sözleşme Metni:
\"\"\"
{contract_text[:15000]}
\"\"\"

Kullanıcı Sorusu: {question}

Bu sözleşmeye dayanarak kullanıcının sorusunu detaylı ve net bir şekilde yanıtla.
Yanıtını sözleşmedeki ilgili maddelere referans vererek yap.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen deneyimli bir hukuk danışmanısın. Sözleşmeler hakkında sorulan soruları detaylı ve anlaşılır şekilde yanıtlarsın."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"❌ Hata: {str(e)}"

def export_json(result):
    """JSON olarak dışa aktar"""
    if result is None:
        return "❌ Önce sözleşmeyi analiz edin!"
    
    json_str = json.dumps(result, indent=2, ensure_ascii=False)
    filename = f"sozlesme_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    return f"✅ Dosya kaydedildi: {filename}"

def export_txt(result):
    """TXT olarak dışa aktar"""
    if result is None:
        return "❌ Önce sözleşmeyi analiz edin!"
    
    text_report = f"""
SÖZLEŞME ANALİZ RAPORU
{'='*60}

Sözleşme Türü: {result.get('contract_type', '-')}
Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}

TARAFLAR
{'-'*60}
Taraf 1: {result.get('parties', {}).get('party_a', '-')}
Taraf 2: {result.get('parties', {}).get('party_b', '-')}

GENEL DEĞERLENDİRME
{'-'*60}
{result.get('overall_assessment', '-')}

KRİTİK NOKTALAR
{'-'*60}
"""
    
    if result.get('critical_points'):
        for i, point in enumerate(result['critical_points'], 1):
            text_report += f"\n{i}. {point.get('category', '-')} (Risk: {point.get('risk_level', '-')})\n"
            text_report += f"   Nokta: {point.get('point', '-')}\n"
            text_report += f"   Öneri: {point.get('recommendation', '-')}\n"
    
    text_report += f"\n\nRİSKLER\n{'-'*60}\n"
    if result.get('risks'):
        for i, risk in enumerate(result['risks'], 1):
            text_report += f"\n{i}. {risk.get('risk', '-')} (Seviye: {risk.get('severity', '-')})\n"
            text_report += f"   Azaltma: {risk.get('mitigation', '-')}\n"
    
    text_report += f"\n\nFİNANSAL ŞARTLAR\n{'-'*60}\n"
    if result.get('financial_terms'):
        for term in result['financial_terms']:
            text_report += f"\n{term.get('term', '-')}: {term.get('amount', '-')}\n"
            text_report += f"Açıklama: {term.get('description', '-')}\n"
    
    filename = f"sozlesme_analiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text_report)
    
    return f"✅ Dosya kaydedildi: {filename}"

# ============================================
# GRADIO INTERFACE
# ============================================

with gr.Blocks(title="Sözleşme Analiz Tool'u", theme=gr.themes.Soft()) as demo:
    
    # State variables
    analysis_result = gr.State(None)
    contract_text_state = gr.State(None)
    
    # Header
    gr.Markdown("""
    # 📄 Sözleşme Analiz Tool'u
    
    **AI destekli sözleşme analizi ve kritik nokta tespiti**
    
    Sözleşmenizi yükleyin, AI otomatik olarak kritik noktaları, riskleri ve yükümlülükleri analiz edecektir.
    """)
    
    # Main content
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Ayarlar")
            
            api_key_input = gr.Textbox(
                label="OpenAI API Key",
                type="password",
                placeholder="sk-...",
                info="OpenAI API anahtarınızı girin"
            )
            
            gr.Markdown("### 📤 Dosya Yükle")
            
            file_input = gr.File(
                label="Sözleşme Dosyası",
                file_types=[".pdf", ".docx", ".txt"],
                type="filepath",
                info="PDF, Word veya TXT formatında sözleşme yükleyebilirsiniz"
            )
            
            analyze_btn = gr.Button("🚀 Analiz Et", variant="primary", size="lg")
            
            gr.Markdown("### 📥 Raporu İndir")
            
            with gr.Row():
                export_json_btn = gr.Button("📄 JSON İndir", size="sm")
                export_txt_btn = gr.Button("📝 TXT İndir", size="sm")
            
            export_status = gr.Textbox(label="Durum", interactive=False)
        
        with gr.Column(scale=2):
            gr.Markdown("### 📊 Analiz Sonuçları")
            
            analysis_output = gr.Markdown(
                value="👆 Lütfen yukarıdan bir sözleşme dosyası yükleyin ve analiz edin.",
                label="Sonuç"
            )
    
    # Question section
    gr.Markdown("---")
    gr.Markdown("### 💬 Sözleşme Hakkında Soru Sor")
    
    with gr.Row():
        question_input = gr.Textbox(
            label="Sorunuz",
            placeholder="Sözleşme hakkında sorunuzu yazın...",
            lines=2
        )
        ask_btn = gr.Button("Sor", variant="secondary")
    
    question_output = gr.Markdown(label="Cevap")
    
    # Example questions
    gr.Markdown("""
    #### 💡 Örnek Sorular
    - Bu sözleşmede ödeme koşulları nedir?
    - Fesih durumunda ne olur?
    - Gizlilik yükümlülükleri nelerdir?
    - Sözleşme süresi ne kadar?
    - Cezai şart var mı?
    - Hangi tarafın daha fazla yükümlülüğü var?
    - Force majeure (mücbir sebep) maddesi var mı?
    - Fikri mülkiyet hakları kime ait?
    """)
    
    # Event handlers
    analyze_btn.click(
        fn=analyze_contract,
        inputs=[file_input, api_key_input],
        outputs=[analysis_output, analysis_result, contract_text_state]
    )
    
    ask_btn.click(
        fn=ask_question,
        inputs=[question_input, contract_text_state, api_key_input],
        outputs=question_output
    )
    
    export_json_btn.click(
        fn=export_json,
        inputs=analysis_result,
        outputs=export_status
    )
    
    export_txt_btn.click(
        fn=export_txt,
        inputs=analysis_result,
        outputs=export_status
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
