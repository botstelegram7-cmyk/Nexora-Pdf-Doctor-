"""
i18n.py — Multi-language support for Nexora PDF Doctor Bot v3
Languages: English, Hindi, Bhojpuri, Spanish, French, Korean
"""

STRINGS = {

    # ── ENGLISH ──────────────────────────────────────────────────────────
    "en": {
        "lang_name": "🇬🇧 English",
        "lang_selected": "✅ Language set to English!",
        "choose_lang": "🌍 Choose your language:",

        "welcome": (
            "👋 <b>Welcome to Nexora PDF Doctor!</b>\n\n"
            "🤖 Your all-in-one PDF toolkit.\n"
            "Use /help to see all features or tap below! 👇"
        ),
        "help_title": "📖 <b>All Commands:</b>",
        "account_title": "👤 <b>My Account</b>",

        "send_pdf": "📎 Please send a PDF file!",
        "send_image": "📎 Please send an image or PDF!",
        "processing": "⏳ Processing...",
        "done": "✅ Done!",
        "error": "❌ Error",
        "cancel": "❌ Cancel · Return to Menu",
        "back": "🏠 Main Menu",

        # OCR
        "ocr_choose_lang": "🌐 <b>Choose the language of your document:</b>",
        "ocr_extracting": "⏳ Extracting text with OCR... 👁️",
        "ocr_done": "👁️ <b>OCR Complete!</b>",
        "ocr_no_text": "⚠️ No text found in document.",

        # Handwriting
        "hw_choose_font": "✍️ <b>Choose Handwriting Font:</b>",
        "hw_choose_style": "📓 <b>Choose Notebook Style:</b>",
        "hw_type_text": "📝 Now type your text:",
        "hw_done": "✍️ <b>Handwritten PDF ready!</b>",

        # Page surgery
        "delete_pages_prompt": "🗑️ Send the PDF, then tell me which pages to delete.\nFormat: <code>2,5,7-9</code>",
        "reorder_prompt": "🔀 Send the PDF, then type the new page order.\nExample: <code>3,1,2</code> or <code>1,3,2-4</code>",
        "extract_prompt": "🔖 Send the PDF to extract pages from!",

        # New features
        "pdf2word_prompt": "📄 Send the PDF to convert to Word (DOCX)!",
        "pdf2word_done": "📄 <b>PDF → Word complete!</b>",
        "pdf2ppt_prompt": "📊 Send the PDF to convert to PowerPoint!",
        "pdf2ppt_done": "📊 <b>PDF → PowerPoint complete!</b>",
        "crop_prompt": "✂️ Send the PDF to crop margins!",
        "crop_done": "✂️ <b>Margins cropped!</b>",
        "qr_prompt": "🔲 Type the text or URL to generate a QR code:",
        "qr_done": "🔲 <b>QR Code generated!</b>",

        # Plan messages
        "free_limit": "⚠️ Free plan: 3 operations/day. Upgrade to Pro for unlimited!",
        "pro_only": "🔒 This feature requires Pro plan.",
        "basic_only": "🔒 This feature requires Basic or Pro plan.",
    },

    # ── HINDI ─────────────────────────────────────────────────────────────
    "hi": {
        "lang_name": "🇮🇳 हिंदी",
        "lang_selected": "✅ भाषा हिंदी में सेट हो गई!",
        "choose_lang": "🌍 अपनी भाषा चुनें:",

        "welcome": (
            "👋 <b>Nexora PDF Doctor में आपका स्वागत है!</b>\n\n"
            "🤖 आपका सम्पूर्ण PDF टूलकिट।\n"
            "सभी फीचर देखने के लिए /help टाइप करें या नीचे टैप करें! 👇"
        ),
        "help_title": "📖 <b>सभी कमांड:</b>",
        "account_title": "👤 <b>मेरा अकाउंट</b>",

        "send_pdf": "📎 कृपया एक PDF फाइल भेजें!",
        "send_image": "📎 कृपया एक इमेज या PDF भेजें!",
        "processing": "⏳ प्रोसेस हो रहा है...",
        "done": "✅ हो गया!",
        "error": "❌ गलती",
        "cancel": "❌ रद्द करें · मेनू पर वापस",
        "back": "🏠 मुख्य मेनू",

        "ocr_choose_lang": "🌐 <b>अपने दस्तावेज़ की भाषा चुनें:</b>",
        "ocr_extracting": "⏳ OCR से टेक्स्ट निकाला जा रहा है... 👁️",
        "ocr_done": "👁️ <b>OCR पूर्ण!</b>",
        "ocr_no_text": "⚠️ दस्तावेज़ में कोई टेक्स्ट नहीं मिला।",

        "hw_choose_font": "✍️ <b>हस्तलेखन फ़ॉन्ट चुनें:</b>",
        "hw_choose_style": "📓 <b>नोटबुक स्टाइल चुनें:</b>",
        "hw_type_text": "📝 अब अपना टेक्स्ट टाइप करें:",
        "hw_done": "✍️ <b>हस्तलिखित PDF तैयार है!</b>",

        "delete_pages_prompt": "🗑️ PDF भेजें, फिर डिलीट करने वाले पेज बताएं।\nफॉर्मेट: <code>2,5,7-9</code>",
        "reorder_prompt": "🔀 PDF भेजें, फिर नया पेज ऑर्डर टाइप करें।\nउदाहरण: <code>3,1,2</code>",
        "extract_prompt": "🔖 पेज निकालने के लिए PDF भेजें!",

        "pdf2word_prompt": "📄 Word (DOCX) में बदलने के लिए PDF भेजें!",
        "pdf2word_done": "📄 <b>PDF → Word पूर्ण!</b>",
        "pdf2ppt_prompt": "📊 PowerPoint में बदलने के लिए PDF भेजें!",
        "pdf2ppt_done": "📊 <b>PDF → PowerPoint पूर्ण!</b>",
        "crop_prompt": "✂️ मार्जिन काटने के लिए PDF भेजें!",
        "crop_done": "✂️ <b>मार्जिन कट गए!</b>",
        "qr_prompt": "🔲 QR कोड के लिए टेक्स्ट या URL टाइप करें:",
        "qr_done": "🔲 <b>QR कोड बन गया!</b>",

        "free_limit": "⚠️ फ्री प्लान: 3 ऑपरेशन/दिन। अनलिमिटेड के लिए Pro लें!",
        "pro_only": "🔒 यह फीचर Pro प्लान में उपलब्ध है।",
        "basic_only": "🔒 यह फीचर Basic या Pro प्लान में उपलब्ध है।",
    },

    # ── BHOJPURI ──────────────────────────────────────────────────────────
    "bh": {
        "lang_name": "🪔 भोजपुरी",
        "lang_selected": "✅ भाषा भोजपुरी में सेट हो गइल!",
        "choose_lang": "🌍 आपन भाषा चुनीं:",

        "welcome": (
            "👋 <b>Nexora PDF Doctor में रउआ के स्वागत बा!</b>\n\n"
            "🤖 रउआ के पूरा PDF टूलकिट।\n"
            "सब फीचर देखे खातिर /help टाइप करीं! 👇"
        ),
        "help_title": "📖 <b>सब कमांड:</b>",
        "account_title": "👤 <b>हमार अकाउंट</b>",

        "send_pdf": "📎 कृपया एगो PDF फाइल भेजीं!",
        "send_image": "📎 एगो इमेज या PDF भेजीं!",
        "processing": "⏳ काम हो रहल बा...",
        "done": "✅ हो गइल!",
        "error": "❌ गलती",
        "cancel": "❌ रद्द करीं",
        "back": "🏠 मुख्य मेनू",

        "ocr_choose_lang": "🌐 <b>आपन कागज के भाषा चुनीं:</b>",
        "ocr_extracting": "⏳ OCR से टेक्स्ट निकलत बा... 👁️",
        "ocr_done": "👁️ <b>OCR पूरा भइल!</b>",
        "ocr_no_text": "⚠️ कवनो टेक्स्ट ना मिलल।",

        "hw_choose_font": "✍️ <b>हाथ के लिखाई वाला फ़ॉन्ट चुनीं:</b>",
        "hw_choose_style": "📓 <b>नोटबुक स्टाइल चुनीं:</b>",
        "hw_type_text": "📝 अब टेक्स्ट टाइप करीं:",
        "hw_done": "✍️ <b>हाथ से लिखल PDF तैयार बा!</b>",

        "delete_pages_prompt": "🗑️ PDF भेजीं, फिर बताईं कवन पेज मिटावल जाय।\nफॉर्मेट: <code>2,5,7-9</code>",
        "reorder_prompt": "🔀 PDF भेजीं, फिर नया पेज क्रम टाइप करीं।",
        "extract_prompt": "🔖 पेज निकाले खातिर PDF भेजीं!",

        "pdf2word_prompt": "📄 Word में बदले खातिर PDF भेजीं!",
        "pdf2word_done": "📄 <b>PDF → Word तैयार!</b>",
        "pdf2ppt_prompt": "📊 PowerPoint में बदले खातिर PDF भेजीं!",
        "pdf2ppt_done": "📊 <b>PDF → PowerPoint तैयार!</b>",
        "crop_prompt": "✂️ मार्जिन काटे खातिर PDF भेजीं!",
        "crop_done": "✂️ <b>मार्जिन कट गइल!</b>",
        "qr_prompt": "🔲 QR कोड खातिर टेक्स्ट या URL टाइप करीं:",
        "qr_done": "🔲 <b>QR कोड बन गइल!</b>",

        "free_limit": "⚠️ फ्री प्लान: 3 काम/दिन। ज्यादा खातिर Pro लीं!",
        "pro_only": "🔒 इ फीचर Pro प्लान में बा।",
        "basic_only": "🔒 इ फीचर Basic या Pro में बा।",
    },

    # ── SPANISH ───────────────────────────────────────────────────────────
    "es": {
        "lang_name": "🇪🇸 Español",
        "lang_selected": "✅ ¡Idioma configurado en Español!",
        "choose_lang": "🌍 Elige tu idioma:",

        "welcome": (
            "👋 <b>¡Bienvenido a Nexora PDF Doctor!</b>\n\n"
            "🤖 Tu kit de herramientas PDF todo en uno.\n"
            "Usa /help para ver todas las funciones o toca abajo! 👇"
        ),
        "help_title": "📖 <b>Todos los comandos:</b>",
        "account_title": "👤 <b>Mi Cuenta</b>",

        "send_pdf": "📎 ¡Por favor envía un archivo PDF!",
        "send_image": "📎 ¡Por favor envía una imagen o PDF!",
        "processing": "⏳ Procesando...",
        "done": "✅ ¡Listo!",
        "error": "❌ Error",
        "cancel": "❌ Cancelar · Volver al Menú",
        "back": "🏠 Menú Principal",

        "ocr_choose_lang": "🌐 <b>Elige el idioma de tu documento:</b>",
        "ocr_extracting": "⏳ Extrayendo texto con OCR... 👁️",
        "ocr_done": "👁️ <b>¡OCR completo!</b>",
        "ocr_no_text": "⚠️ No se encontró texto en el documento.",

        "hw_choose_font": "✍️ <b>Elige la fuente de escritura a mano:</b>",
        "hw_choose_style": "📓 <b>Elige el estilo de cuaderno:</b>",
        "hw_type_text": "📝 Ahora escribe tu texto:",
        "hw_done": "✍️ <b>¡PDF manuscrito listo!</b>",

        "delete_pages_prompt": "🗑️ Envía el PDF y dime qué páginas eliminar.\nFormato: <code>2,5,7-9</code>",
        "reorder_prompt": "🔀 Envía el PDF y escribe el nuevo orden.\nEjemplo: <code>3,1,2</code>",
        "extract_prompt": "🔖 ¡Envía el PDF para extraer páginas!",

        "pdf2word_prompt": "📄 ¡Envía el PDF para convertir a Word (DOCX)!",
        "pdf2word_done": "📄 <b>¡PDF → Word completado!</b>",
        "pdf2ppt_prompt": "📊 ¡Envía el PDF para convertir a PowerPoint!",
        "pdf2ppt_done": "📊 <b>¡PDF → PowerPoint completado!</b>",
        "crop_prompt": "✂️ ¡Envía el PDF para recortar márgenes!",
        "crop_done": "✂️ <b>¡Márgenes recortados!</b>",
        "qr_prompt": "🔲 Escribe el texto o URL para generar un código QR:",
        "qr_done": "🔲 <b>¡Código QR generado!</b>",

        "free_limit": "⚠️ Plan gratis: 3 operaciones/día. ¡Actualiza a Pro para ilimitado!",
        "pro_only": "🔒 Esta función requiere el plan Pro.",
        "basic_only": "🔒 Esta función requiere el plan Basic o Pro.",
    },

    # ── FRENCH ────────────────────────────────────────────────────────────
    "fr": {
        "lang_name": "🇫🇷 Français",
        "lang_selected": "✅ Langue configurée en Français!",
        "choose_lang": "🌍 Choisissez votre langue:",

        "welcome": (
            "👋 <b>Bienvenue sur Nexora PDF Doctor!</b>\n\n"
            "🤖 Votre boîte à outils PDF tout-en-un.\n"
            "Utilisez /help pour voir toutes les fonctionnalités! 👇"
        ),
        "help_title": "📖 <b>Toutes les commandes:</b>",
        "account_title": "👤 <b>Mon Compte</b>",

        "send_pdf": "📎 Veuillez envoyer un fichier PDF!",
        "send_image": "📎 Veuillez envoyer une image ou un PDF!",
        "processing": "⏳ Traitement en cours...",
        "done": "✅ Terminé!",
        "error": "❌ Erreur",
        "cancel": "❌ Annuler · Retour au Menu",
        "back": "🏠 Menu Principal",

        "ocr_choose_lang": "🌐 <b>Choisissez la langue de votre document:</b>",
        "ocr_extracting": "⏳ Extraction du texte par OCR... 👁️",
        "ocr_done": "👁️ <b>OCR terminé!</b>",
        "ocr_no_text": "⚠️ Aucun texte trouvé dans le document.",

        "hw_choose_font": "✍️ <b>Choisissez la police manuscrite:</b>",
        "hw_choose_style": "📓 <b>Choisissez le style de cahier:</b>",
        "hw_type_text": "📝 Tapez maintenant votre texte:",
        "hw_done": "✍️ <b>PDF manuscrit prêt!</b>",

        "delete_pages_prompt": "🗑️ Envoyez le PDF puis indiquez les pages à supprimer.\nFormat: <code>2,5,7-9</code>",
        "reorder_prompt": "🔀 Envoyez le PDF puis tapez le nouvel ordre.\nExemple: <code>3,1,2</code>",
        "extract_prompt": "🔖 Envoyez le PDF pour extraire des pages!",

        "pdf2word_prompt": "📄 Envoyez le PDF à convertir en Word (DOCX)!",
        "pdf2word_done": "📄 <b>PDF → Word terminé!</b>",
        "pdf2ppt_prompt": "📊 Envoyez le PDF à convertir en PowerPoint!",
        "pdf2ppt_done": "📊 <b>PDF → PowerPoint terminé!</b>",
        "crop_prompt": "✂️ Envoyez le PDF pour rogner les marges!",
        "crop_done": "✂️ <b>Marges rognées!</b>",
        "qr_prompt": "🔲 Tapez le texte ou l'URL pour générer un QR code:",
        "qr_done": "🔲 <b>QR Code généré!</b>",

        "free_limit": "⚠️ Plan gratuit: 3 opérations/jour. Passez à Pro pour illimité!",
        "pro_only": "🔒 Cette fonctionnalité nécessite le plan Pro.",
        "basic_only": "🔒 Cette fonctionnalité nécessite le plan Basic ou Pro.",
    },

    # ── KOREAN ────────────────────────────────────────────────────────────
    "ko": {
        "lang_name": "🇰🇷 한국어",
        "lang_selected": "✅ 언어가 한국어로 설정되었습니다!",
        "choose_lang": "🌍 언어를 선택하세요:",

        "welcome": (
            "👋 <b>Nexora PDF Doctor에 오신 것을 환영합니다!</b>\n\n"
            "🤖 올인원 PDF 툴킷입니다.\n"
            "모든 기능을 보려면 /help를 사용하거나 아래를 탭하세요! 👇"
        ),
        "help_title": "📖 <b>모든 명령어:</b>",
        "account_title": "👤 <b>내 계정</b>",

        "send_pdf": "📎 PDF 파일을 보내주세요!",
        "send_image": "📎 이미지 또는 PDF를 보내주세요!",
        "processing": "⏳ 처리 중...",
        "done": "✅ 완료!",
        "error": "❌ 오류",
        "cancel": "❌ 취소 · 메뉴로 돌아가기",
        "back": "🏠 메인 메뉴",

        "ocr_choose_lang": "🌐 <b>문서 언어를 선택하세요:</b>",
        "ocr_extracting": "⏳ OCR로 텍스트 추출 중... 👁️",
        "ocr_done": "👁️ <b>OCR 완료!</b>",
        "ocr_no_text": "⚠️ 문서에서 텍스트를 찾을 수 없습니다.",

        "hw_choose_font": "✍️ <b>손글씨 폰트를 선택하세요:</b>",
        "hw_choose_style": "📓 <b>노트북 스타일을 선택하세요:</b>",
        "hw_type_text": "📝 이제 텍스트를 입력하세요:",
        "hw_done": "✍️ <b>손글씨 PDF 완성!</b>",

        "delete_pages_prompt": "🗑️ PDF를 보내고 삭제할 페이지를 알려주세요.\n형식: <code>2,5,7-9</code>",
        "reorder_prompt": "🔀 PDF를 보내고 새 페이지 순서를 입력하세요.\n예: <code>3,1,2</code>",
        "extract_prompt": "🔖 페이지를 추출할 PDF를 보내세요!",

        "pdf2word_prompt": "📄 Word(DOCX)로 변환할 PDF를 보내세요!",
        "pdf2word_done": "📄 <b>PDF → Word 완료!</b>",
        "pdf2ppt_prompt": "📊 PowerPoint로 변환할 PDF를 보내세요!",
        "pdf2ppt_done": "📊 <b>PDF → PowerPoint 완료!</b>",
        "crop_prompt": "✂️ 여백을 잘라낼 PDF를 보내세요!",
        "crop_done": "✂️ <b>여백이 잘렸습니다!</b>",
        "qr_prompt": "🔲 QR 코드를 생성할 텍스트 또는 URL을 입력하세요:",
        "qr_done": "🔲 <b>QR 코드 생성 완료!</b>",

        "free_limit": "⚠️ 무료 플랜: 하루 3회 제한. 무제한은 Pro로 업그레이드!",
        "pro_only": "🔒 이 기능은 Pro 플랜이 필요합니다.",
        "basic_only": "🔒 이 기능은 Basic 또는 Pro 플랜이 필요합니다.",
    },
}

DEFAULT_LANG = "en"

def t(ctx, key: str) -> str:
    """Get translated string for user's language."""
    lang = ctx.user_data.get("lang", DEFAULT_LANG) if ctx and ctx.user_data else DEFAULT_LANG
    lang_strings = STRINGS.get(lang, STRINGS[DEFAULT_LANG])
    return lang_strings.get(key, STRINGS[DEFAULT_LANG].get(key, key))

def get_user_lang(ctx) -> str:
    if ctx and ctx.user_data:
        return ctx.user_data.get("lang", DEFAULT_LANG)
    return DEFAULT_LANG

def set_user_lang(ctx, lang: str):
    if lang in STRINGS:
        ctx.user_data["lang"] = lang
