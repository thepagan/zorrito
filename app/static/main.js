function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const newTheme = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("zorrito-theme", newTheme);
}

async function loadCounties() {
  const state = document.getElementById('state').value;
  const countySelect = document.getElementById('fips');
  countySelect.innerHTML = '';
  try {
    const res = await fetch('/counties/' + state);
    if (!res.ok) throw new Error("Network response was not ok");
    const counties = await res.json();
    counties.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.fips;
      opt.textContent = c.name;
      countySelect.appendChild(opt);
    });
  } catch (error) {
    console.error("Error loading counties:", error);
  }
}

window.toggleTheme = toggleTheme;
window.loadCounties = loadCounties;

window.addEventListener('DOMContentLoaded', () => {
  if (!window.matchMedia('(prefers-color-scheme)').media !== 'not all') {
    const hour = new Date().getHours();
    const darkMode = hour < 6 || hour >= 18;
    if (darkMode) {
      document.documentElement.style.setProperty('--bg-color', '#121212');
      document.documentElement.style.setProperty('--text-color', '#f1f1f1');
      document.documentElement.style.setProperty('--accent-color', '#66aaff');
    }
  }

  const translations = {
    en: {
      "title": "🦊 Alert Registration",
      "phone_label": "Phone Number",
      "state_label": "State",
      "county_label": "County",
      "language_label": "Language",
      "subscribe_label": "I want to receive alerts",
      "submit_btn": "Register",
      "theme_btn": "Toggle Theme"
    },
    es: {
      "title": "🦊 Registro de Alertas",
      "phone_label": "Número de Teléfono",
      "state_label": "Estado",
      "county_label": "Condado",
      "language_label": "Idioma",
      "subscribe_label": "Deseo recibir alertas",
      "submit_btn": "Registrarme",
      "theme_btn": "Cambiar Tema"
    },
    so: {
      "title": "🦊 Diiwaangelinta Digniinaha",
      "phone_label": "Lambarka Taleefanka",
      "state_label": "Gobol",
      "county_label": "Degmo",
      "language_label": "Luuqad",
      "subscribe_label": "Waxaan rabaa in aan helo digniino",
      "submit_btn": "Diiwaangeli",
      "theme_btn": "Beddel Mowduuca"
    },
    ar: {
      "title": "🦊 تسجيل التنبيهات",
      "phone_label": "رقم الهاتف",
      "state_label": "الولاية",
      "county_label": "المقاطعة",
      "language_label": "اللغة",
      "subscribe_label": "أرغب في تلقي التنبيهات",
      "submit_btn": "سجل",
      "theme_btn": "تبديل السمة"
    },
    sw: {
      "title": "🦊 Usajili wa Tahadhari",
      "phone_label": "Nambari ya Simu",
      "state_label": "Jimbo",
      "county_label": "Kaunti",
      "language_label": "Lugha",
      "subscribe_label": "Ningependa kupokea tahadhari",
      "submit_btn": "Jisajili",
      "theme_btn": "Badilisha Mandhari"
    },
    fr: {
      "title": "🦊 Inscription aux Alertes",
      "phone_label": "Numéro de Téléphone",
      "state_label": "État",
      "county_label": "Comté",
      "language_label": "Langue",
      "subscribe_label": "Je souhaite recevoir des alertes",
      "submit_btn": "S'inscrire",
      "theme_btn": "Changer de Thème"
    },
    rw: {
      "title": "🦊 Kwiyandikisha kuburira",
      "phone_label": "Numero ya Telefoni",
      "state_label": "Intara",
      "county_label": "Akarere",
      "language_label": "Ururimi",
      "subscribe_label": "Ndashaka kwakira amakuru y'uburira",
      "submit_btn": "Iyandikishe",
      "theme_btn": "Hindura insanganyamatsiko"
    },
    vi: {
      "title": "🦊 Đăng ký Cảnh báo",
      "phone_label": "Số Điện Thoại",
      "state_label": "Tiểu Bang",
      "county_label": "Quận",
      "language_label": "Ngôn ngữ",
      "subscribe_label": "Tôi muốn nhận cảnh báo",
      "submit_btn": "Đăng ký",
      "theme_btn": "Chuyển Giao Diện"
    },
    ne: {
      "title": "🦊 सूचना दर्ता",
      "phone_label": "फोन नम्बर",
      "state_label": "राज्य",
      "county_label": "जिल्ला",
      "language_label": "भाषा",
      "subscribe_label": "म सूचना प्राप्त गर्न चाहन्छु",
      "submit_btn": "दर्ता गर्नुहोस्",
      "theme_btn": "थिम परिवर्तन गर्नुहोस्"
    },
    te: {
      "title": "🦊 హెచ్చరిక నమోదు",
      "phone_label": "ఫోన్ నంబర్",
      "state_label": "రాష్ట్రం",
      "county_label": "జిల్లా",
      "language_label": "భాష",
      "subscribe_label": "నేను హెచ్చరికలు అందుకోవాలనుకుంటున్నాను",
      "submit_btn": "నమోదు చేయండి",
      "theme_btn": "థీమ్ మార్చండి"
    },
    tr: {
      "title": "🦊 Uyarı Kaydı",
      "phone_label": "Telefon Numarası",
      "state_label": "Eyalet",
      "county_label": "İlçe",
      "language_label": "Dil",
      "subscribe_label": "Uyarılar almak istiyorum",
      "submit_btn": "Kaydol",
      "theme_btn": "Temayı Değiştir"
    },
    ps: {
      "title": "🦊 د خبرداري راجسټریشن",
      "phone_label": "د تلیفون شمېره",
      "state_label": "ایالت",
      "county_label": "ولسوالۍ",
      "language_label": "ژبه",
      "subscribe_label": "زه غواړم چې خبرداری ترلاسه کړم",
      "submit_btn": "راجستر",
      "theme_btn": "تیم بدل کړئ"
    }
  };

  function updateText(lang) {
    document.querySelector('[data-i18n="title"]').textContent = translations[lang].title;
    document.querySelector('[data-i18n="phone_label"]').textContent = translations[lang].phone_label;
    document.querySelector('[data-i18n="state_label"]').textContent = translations[lang].state_label;
    document.querySelector('[data-i18n="county_label"]').textContent = translations[lang].county_label;
    document.querySelector('[data-i18n="language_label"]').textContent = translations[lang].language_label;
    document.querySelector('[data-i18n="subscribe_label"]').textContent = translations[lang].subscribe_label;
    document.querySelector('[data-i18n="submit_btn"]').textContent = translations[lang].submit_btn;
    document.querySelector('[data-i18n="theme_btn"]').textContent = translations[lang].theme_btn;
  }

  const langSelect = document.getElementById("language");
  if (langSelect) {
    const browserLang = navigator.language.startsWith("es") ? "es" : "en";
    langSelect.value = browserLang;
    updateText(browserLang);
    langSelect.addEventListener("change", (e) => {
      updateText(e.target.value);
    });
  }

  const stateSelect = document.getElementById("state");
  if (stateSelect) {
    stateSelect.addEventListener("change", loadCounties);
  }
});