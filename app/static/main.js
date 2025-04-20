function applyThemeStyles(theme) {
  const isDark = theme === "dark";

  document.documentElement.style.setProperty('--bg-color', isDark ? '#121212' : '#ffffff');
  document.documentElement.style.setProperty('--text-color', isDark ? '#f1f1f1' : '#000000');
  document.documentElement.style.setProperty('--accent-color', isDark ? '#66aaff' : '#0066cc');

  document.querySelectorAll('.themed-form').forEach(el => {
    el.style.backgroundColor = isDark ? '#1e1e1e' : '#ffffff';
    el.style.color = isDark ? '#f1f1f1' : '#000000';
  });

  document.querySelectorAll('label').forEach(label => {
    label.style.color = isDark ? '#f1f1f1' : '#000000';
  });

  const header = document.querySelector('[data-i18n="title"]');
  if (header) header.style.color = isDark ? '#f1f1f1' : '#000000';

  document.querySelectorAll('.themed-input').forEach(el => {
    el.style.backgroundColor = isDark ? '#2a2a2a' : '#ffffff';
    el.style.color = isDark ? '#f1f1f1' : '#000000';
    el.style.borderColor = isDark ? '#555' : '#ccc';
  });

  document.querySelectorAll('.btn-primary').forEach(el => {
    el.style.backgroundColor = isDark ? '#333' : '#007bff';
    el.style.color = isDark ? '#fff' : '#ffffff';
    el.style.border = 'none';
  });
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const newTheme = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("zorrito-theme", newTheme);
  applyThemeStyles(newTheme);
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
  let theme = localStorage.getItem("zorrito-theme");

  // If no saved preference, detect system preference
  if (!theme) {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      theme = "dark";
    } else {
      theme = "light";
    }
  }

  document.documentElement.setAttribute("data-theme", theme);
  applyThemeStyles(theme);

  const translations = {
    en: {
      "title": "🦊 Alert Registration",
      "phone_label": "Phone Number",
      "state_label": "State",
      "county_label": "County",
      "language_label": "Language",
      "subscribe_label": "I want to receive alerts",
      "submit_btn": "Subscribe to Alerts",
      "theme_btn": "Toggle Theme",
      "unsubscribe_label": "I no longer want to receive alerts",
      "unsubscribe_btn": "Unsubscribe from Alerts"
    },
    es: {
      "title": "🦊 Registro de Alertas",
      "phone_label": "Número de Teléfono",
      "state_label": "Estado",
      "county_label": "Condado",
      "language_label": "Idioma",
      "subscribe_label": "Deseo recibir alertas",
      "submit_btn": "Suscribirse a alertas",
      "theme_btn": "Cambiar Tema",
      "unsubscribe_label": "Ya no quiero recibir alertas",
      "unsubscribe_btn": "Darse de baja de Alertas"
    },
    so: {
      "title": "🦊 Diiwaangelinta Digniinaha",
      "phone_label": "Lambarka Taleefanka",
      "state_label": "Gobol",
      "county_label": "Degmo",
      "language_label": "Luuqad",
      "subscribe_label": "Waxaan rabaa in aan helo digniino",
      "submit_btn": "Ku biir digniinta",
      "theme_btn": "Beddel Mowduuca",
      "unsubscribe_label": "Ma rabto in aan helo digniino",
      "unsubscribe_btn": "Ka bax digniino"
    },
    ar: {
      "title": "🦊 تسجيل التنبيهات",
      "phone_label": "رقم الهاتف",
      "state_label": "الولاية",
      "county_label": "المقاطعة",
      "language_label": "اللغة",
      "subscribe_label": "أرغب في تلقي التنبيهات",
      "submit_btn": "اشترك في التنبيهات",
      "theme_btn": "تبديل السمة",
      "unsubscribe_label": "لم أعد أرغب في تلقي التنبيهات",
      "unsubscribe_btn": "إلغاء الاشتراك في التنبيهات"
    },
    sw: {
      "title": "🦊 Usajili wa Tahadhari",
      "phone_label": "Nambari ya Simu",
      "state_label": "Jimbo",
      "county_label": "Kaunti",
      "language_label": "Lugha",
      "subscribe_label": "Ningependa kupokea tahadhari",
      "submit_btn": "Jiandikishe kwa arifa",
      "theme_btn": "Badilisha Mandhari",
      "unsubscribe_label": "Sitaki kupokea tahadhari tena",
      "unsubscribe_btn": "Jiondoe kwenye Tahadhari"
    },
    fr: {
      "title": "🦊 Inscription aux Alertes",
      "phone_label": "Numéro de Téléphone",
      "state_label": "État",
      "county_label": "Comté",
      "language_label": "Langue",
      "subscribe_label": "Je souhaite recevoir des alertes",
      "submit_btn": "S'abonner aux alertes",
      "theme_btn": "Changer de Thème",
      "unsubscribe_label": "Je ne veux plus recevoir d'alertes",
      "unsubscribe_btn": "Se désinscrire des alertes"
    },
    rw: {
      "title": "🦊 Kwiyandikisha kuburira",
      "phone_label": "Numero ya Telefoni",
      "state_label": "Intara",
      "county_label": "Akarere",
      "language_label": "Ururimi",
      "subscribe_label": "Ndashaka kwakira amakuru y'uburira",
      "submit_btn": "Iyandikishe ku butumwa bwo kuburira",
      "theme_btn": "Hindura insanganyamatsiko",
      "unsubscribe_label": "Sinshaka kwakira amakuru y'uburira",
      "unsubscribe_btn": "Kuvana mu burira"
    },
    vi: {
      "title": "🦊 Đăng ký Cảnh báo",
      "phone_label": "Số Điện Thoại",
      "state_label": "Tiểu Bang",
      "county_label": "Quận",
      "language_label": "Ngôn ngữ",
      "subscribe_label": "Tôi muốn nhận cảnh báo",
      "submit_btn": "Đăng ký cảnh báo",
      "theme_btn": "Chuyển Giao Diện",
      "unsubscribe_label": "Tôi không muốn nhận cảnh báo nữa",
      "unsubscribe_btn": "Hủy đăng ký nhận cảnh báo"
    },
    ne: {
      "title": "🦊 सूचना दर्ता",
      "phone_label": "फोन नम्बर",
      "state_label": "राज्य",
      "county_label": "जिल्ला",
      "language_label": "भाषा",
      "subscribe_label": "म सूचना प्राप्त गर्न चाहन्छु",
      "submit_btn": "सूचना सदस्यता लिनुहोस्",
      "theme_btn": "थिम परिवर्तन गर्नुहोस्",
      "unsubscribe_label": "म अब सूचना प्राप्त गर्न चाहन्न",
      "unsubscribe_btn": "सूचनाबाट बाहिर निस्कनुहोस्"
    },
    te: {
      "title": "🦊 హెచ్చరిక నమోదు",
      "phone_label": "ఫోన్ నంబర్",
      "state_label": "రాష్ట్రం",
      "county_label": "జిల్లా",
      "language_label": "భాష",
      "subscribe_label": "నేను హెచ్చరికలు అందుకోవాలనుకుంటున్నాను",
      "submit_btn": "హెచ్చరికల కోసం సబ్స్క్రైబ్ చేయండి",
      "theme_btn": "థీమ్ మార్చండి",
      "unsubscribe_label": "నేను ఇక హెచ్చరికలు అందుకోవడం కోరుకోను",
      "unsubscribe_btn": "హెచ్చరికల నుండి అన్‌సబ్ చేయండి"
    },
    tr: {
      "title": "🦊 Uyarı Kaydı",
      "phone_label": "Telefon Numarası",
      "state_label": "Eyalet",
      "county_label": "İlçe",
      "language_label": "Dil",
      "subscribe_label": "Uyarılar almak istiyorum",
      "submit_btn": "Uyarılara abone ol",
      "theme_btn": "Temayı Değiştir",
      "unsubscribe_label": "Artık uyarı almak istemiyorum",
      "unsubscribe_btn": "Uyarılardan Çık"
    },
    ps: {
      "title": "🦊 د خبرداري راجسټریشن",
      "phone_label": "د تلیفون شمېره",
      "state_label": "ایالت",
      "county_label": "ولسوالۍ",
      "language_label": "ژبه",
      "subscribe_label": "زه غواړم چې خبرداری ترلاسه کړم",
      "submit_btn": "د خبرتیاوو لپاره ګډون وکړئ",
      "theme_btn": "تیم بدل کړئ",
      "unsubscribe_label": "زه نور خبرداری نه غواړم",
      "unsubscribe_btn": "د خبرداریو نه ځان خلاص کړئ"
    }
  };

  function updateText(lang) {
    document.querySelector('[data-i18n="title"]').textContent = translations[lang].title;
    document.title = translations[lang].title;
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

  function showPhoneExistsWarning(lang) {
    const messages = {
      en: {
        warning: "This phone number is already registered.",
        unsubscribe_label: "I no longer want to receive alerts",
        unsubscribe_btn: "Unsubscribe from Alerts"
      },
      es: {
        warning: "Este número de teléfono ya está registrado.",
        unsubscribe_label: "Ya no quiero recibir alertas",
        unsubscribe_btn: "Darse de baja de Alertas"
      },
      so: {
        warning: "Lambarkan taleefanka horey ayaa loo diiwaan geliyay.",
        unsubscribe_label: "Ma rabto in aan helo digniino",
        unsubscribe_btn: "Ka bax digniino"
      },
      ar: {
        warning: "رقم الهاتف هذا مسجل بالفعل.",
        unsubscribe_label: "لم أعد أرغب في تلقي التنبيهات",
        unsubscribe_btn: "إلغاء الاشتراك في التنبيهات"
      },
      sw: {
        warning: "Nambari hii ya simu tayari imesajiliwa.",
        unsubscribe_label: "Sitaki kupokea tahadhari tena",
        unsubscribe_btn: "Jiondoe kwenye Tahadhari"
      },
      fr: {
        warning: "Ce numéro de téléphone est déjà enregistré.",
        unsubscribe_label: "Je ne veux plus recevoir d'alertes",
        unsubscribe_btn: "Se désinscrire des alertes"
      },
      rw: {
        warning: "Uyu mubare w’itumanaho waramaze kwiyandikwa.",
        unsubscribe_label: "Sinshaka kwakira amakuru y'uburira",
        unsubscribe_btn: "Kuvana mu burira"
      },
      vi: {
        warning: "Số điện thoại này đã được đăng ký.",
        unsubscribe_label: "Tôi không muốn nhận cảnh báo nữa",
        unsubscribe_btn: "Hủy đăng ký nhận cảnh báo"
      },
      ne: {
        warning: "यो फोन नम्बर पहिले नै दर्ता गरिएको छ।",
        unsubscribe_label: "म अब सूचना प्राप्त गर्न चाहन्न",
        unsubscribe_btn: "सूचनाबाट बाहिर निस्कनुहोस्"
      },
      te: {
        warning: "ఈ ఫోన్ నంబర్ ఇప్పటికే నమోదు చేయబడింది.",
        unsubscribe_label: "నేను ఇక హెచ్చరికలు అందుకోవడం కోరుకోను",
        unsubscribe_btn: "హెచ్చరికల నుండి అన్‌సబ్ చేయండి"
      },
      tr: {
        warning: "Bu telefon numarası zaten kayıtlı.",
        unsubscribe_label: "Artık uyarı almak istemiyorum",
        unsubscribe_btn: "Uyarılardan Çık"
      },
      ps: {
        warning: "دا د تلیفون شمېره مخکې ثبت شوې ده.",
        unsubscribe_label: "زه نور خبرداری نه غواړم",
        unsubscribe_btn: "د خبرداریو نه ځان خلاص کړئ"
      }
    };
    const language = document.getElementById("language")?.value || "en";
    const phoneWarning = document.getElementById("phone-warning");
    if (phoneWarning) {
      phoneWarning.textContent = messages[language].warning || messages["en"].warning;
      phoneWarning.style.display = "block";
      const checkboxLabel = document.querySelector('label[for="subscribed"]');
      const submitButton = document.querySelector('button[type="submit"]');
      if (checkboxLabel) {
        checkboxLabel.textContent = messages[language].unsubscribe_label || messages["en"].unsubscribe_label;
      }
      if (submitButton) {
        submitButton.textContent = messages[language].unsubscribe_btn || messages["en"].unsubscribe_btn;
      }
    }
  }

  window.showPhoneExistsWarning = showPhoneExistsWarning;

  const logBox = document.getElementById("log-box");
  async function fetchLogs() {
    try {
      const res = await fetch("/logs/recent");
      if (!res.ok) throw new Error("Network response was not ok");
      const data = await res.json();
      if (logBox) {
        logBox.textContent = data.log.join("\n");
        logBox.scrollTop = logBox.scrollHeight;
      }
    } catch (err) {
      console.error("Failed to fetch logs:", err);
      if (logBox) {
        logBox.textContent = "⚠️ Error fetching logs.";
      }
    }
  }

  setInterval(fetchLogs, 5000);
  fetchLogs(); // initial load
});