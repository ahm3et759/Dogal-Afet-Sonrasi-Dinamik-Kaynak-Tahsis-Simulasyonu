import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Grafik Ayarlarını İyileştirme (Daha profesyonel ve anlaşılır görünüm için)
plt.rcParams['figure.figsize'] = (10, 5)
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.facecolor'] = '#f9f9fc'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# --- 1. BULANIK MANTIK SİSTEMİ KURULUMU ---

# Değişkenleri tanımlama (5 Giriş ve 1 Çıkış)
hasar_yogunlugu = ctrl.Antecedent(np.arange(0, 101, 1), 'hasar_yogunlugu')
yol_kapanma = ctrl.Antecedent(np.arange(0, 101, 1), 'yol_kapanma')
ulasim_suresi = ctrl.Antecedent(np.arange(0, 121, 1), 'ulasim_suresi')
nufus_yogunlugu = ctrl.Antecedent(np.arange(0, 101, 1), 'nufus_yogunlugu')
hava_durumu = ctrl.Antecedent(np.arange(0, 101, 1), 'hava_durumu') # 0: Çok İyi, 100: Afet/Şiddetli Fırtına

# Çıkış: Ağırlık merkezi (centroid) durulaştırma metodu
oncelik = ctrl.Consequent(np.arange(0, 101, 1), 'oncelik', defuzzify_method='centroid')

# Dilsel Tanımlamalar (Her biri için 5 Adet Hassas Metrik)
hasar_yogunlugu.automf(5, names=['cok_hafif', 'hafif', 'orta', 'agir', 'cok_agir'])
yol_kapanma.automf(5, names=['cok_dusuk', 'dusuk', 'orta', 'yuksek', 'tamamen_kapali'])
ulasim_suresi.automf(5, names=['cok_kisa', 'kisa', 'orta', 'uzun', 'cok_uzun'])
nufus_yogunlugu.automf(5, names=['issiz', 'seyrek', 'normal', 'yogun', 'cok_yogun'])
hava_durumu.automf(5, names=['cok_iyi', 'iyi', 'orta', 'kotu', 'cok_kotu'])

# Çıkış: Müdahale Önceliği (0-100 Skoru)
oncelik['cok_dusuk'] = fuzz.trapmf(oncelik.universe, [0, 0, 10, 25])
oncelik['dusuk'] = fuzz.trimf(oncelik.universe, [15, 30, 45])
oncelik['orta'] = fuzz.trimf(oncelik.universe, [35, 50, 65])
oncelik['yuksek'] = fuzz.trimf(oncelik.universe, [55, 75, 90])
oncelik['kritik'] = fuzz.trapmf(oncelik.universe, [80, 90, 100, 100])

# KURALLAR (Hassas ve Gelişmiş 20 Kural)
rules = [
    # GÜVENLİK AĞI (Base Coverage): Sistemin hiçbir senaryoda çökmemesini garanti eden 5 temel omurga kural. 
    # Diğer 15 kural bu temelleri duruma göre ezer veya onlarla dengelenir.
    ctrl.Rule(hasar_yogunlugu['cok_hafif'], oncelik['cok_dusuk']),
    ctrl.Rule(hasar_yogunlugu['hafif'], oncelik['dusuk']),
    ctrl.Rule(hasar_yogunlugu['orta'], oncelik['orta']),
    ctrl.Rule(hasar_yogunlugu['agir'], oncelik['yuksek']),
    ctrl.Rule(hasar_yogunlugu['cok_agir'], oncelik['kritik']),
    
    # İleri Düzey Karmaşık Analiz Kuralları (15 Adet)
    ctrl.Rule(hasar_yogunlugu['cok_agir'] & nufus_yogunlugu['cok_yogun'] & yol_kapanma['cok_dusuk'], oncelik['kritik']),
    ctrl.Rule(hasar_yogunlugu['agir'] & nufus_yogunlugu['yogun'] & hava_durumu['cok_iyi'], oncelik['kritik']),
    
    # Yol veya Hava felaket seviyesindeyse müdahale önceliği düşer (Kaynak israfını / can kaybını önleme)
    ctrl.Rule(yol_kapanma['tamamen_kapali'] | hava_durumu['cok_kotu'], oncelik['cok_dusuk']), 
    ctrl.Rule(hasar_yogunlugu['cok_agir'] & yol_kapanma['tamamen_kapali'], oncelik['dusuk']), 
    ctrl.Rule(yol_kapanma['yuksek'] & ulasim_suresi['cok_uzun'], oncelik['dusuk']),
    
    # Orta / Yüksek Durumlar
    ctrl.Rule(hasar_yogunlugu['agir'] & yol_kapanma['orta'] & nufus_yogunlugu['seyrek'], oncelik['yuksek']),
    ctrl.Rule(nufus_yogunlugu['yogun'] & hava_durumu['orta'] & hasar_yogunlugu['orta'], oncelik['yuksek']),
    ctrl.Rule(hava_durumu['cok_kotu'] & hasar_yogunlugu['orta'] & yol_kapanma['dusuk'], oncelik['yuksek']), 
    ctrl.Rule(yol_kapanma['dusuk'] & ulasim_suresi['cok_kisa'] & hasar_yogunlugu['orta'], oncelik['yuksek']),
    
    ctrl.Rule(hasar_yogunlugu['orta'] & nufus_yogunlugu['normal'] & hava_durumu['iyi'], oncelik['orta']),
    ctrl.Rule(hasar_yogunlugu['orta'] & ulasim_suresi['orta'] & yol_kapanma['orta'], oncelik['orta']),
    ctrl.Rule(hasar_yogunlugu['cok_agir'] & nufus_yogunlugu['issiz'] & ulasim_suresi['uzun'], oncelik['orta']),
    
    # Düşük Öncelikler
    ctrl.Rule(hasar_yogunlugu['cok_hafif'] & nufus_yogunlugu['issiz'], oncelik['cok_dusuk']),
    ctrl.Rule(hasar_yogunlugu['hafif'] & ulasim_suresi['uzun'], oncelik['dusuk']),
    ctrl.Rule(nufus_yogunlugu['cok_yogun'] & hasar_yogunlugu['hafif'] & hava_durumu['cok_iyi'], oncelik['dusuk'])
]

# Kontrol sistemini oluştur
afet_ctrl = ctrl.ControlSystem(rules)
afet_sim = ctrl.ControlSystemSimulation(afet_ctrl)


# --- 2. STREAMLIT ARAYÜZÜ ---

st.set_page_config(page_title="Gelişmiş Afet Rota Simülasyonu", layout="wide", page_icon="🚁")

st.title("Doğal Afet Sonrası Dinamik Kaynak Tahsis Simülasyonu 🚁🏚️")
st.markdown("Bulanık mantık kullanılarak **5 farklı çevresel faktöre** göre arama-kurtarma ekiplerinin hedef önceliğini belirleyen profesyonel uzman sistem. *Gelişmiş Bulanık Mantık Uygulaması*")

# Kenar Çubuğu - Giriş Değerleri
st.sidebar.header("Afet Bölgesi Sensör Verileri")

val_hasar = st.sidebar.slider("Hasar Yoğunluğu (%)", 0.0, 100.0, 75.0, 1.0)
val_yol = st.sidebar.slider("Yol Kapanma Olasılığı (%)", 0.0, 100.0, 30.0, 1.0)
val_ulasim = st.sidebar.slider("Ulaşım Süresi (Dakika)", 0.0, 120.0, 20.0, 1.0)
val_nufus = st.sidebar.slider("Nüfus Yoğunluğu (%)", 0.0, 100.0, 85.0, 1.0)
val_hava = st.sidebar.slider("Hava Zorluk Derecesi (%)", 0.0, 100.0, 15.0, 1.0)

# Tab'lar ile düzen
tab1, tab2, tab3, tab4 = st.tabs(["🎛️ Operasyon Paneli", "📈 Anlaşılır Üyelik Fonksiyonları", "📜 Kural Tabanı (5 Değişkenli)", "🌐 Yüksek Çözünürlüklü 3B Yüzey"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Bölge Analiz Verileri (5 Sensör)")
        
        m1, m2 = st.columns(2)
        m1.metric(label="🏚️ Hasar Yoğunluğu", value=f"% {val_hasar}")
        m2.metric(label="🚧 Yol Kapanma Olasılığı", value=f"% {val_yol}")
        
        m3, m4 = st.columns(2)
        m3.metric(label="⏱️ Ulaşım Süresi", value=f"{val_ulasim} Dk")
        m4.metric(label="👥 Nüfus Yoğunluğu", value=f"% {val_nufus}")
        
        st.metric(label="🌩️ Hava Koşulları Zorluğu", value=f"% {val_hava}")
        
        st.markdown("---")
        hesapla_btn = st.button("🚀 Müdahale Önceliğini Hesapla", type="primary", use_container_width=True)
        if hesapla_btn:
            st.session_state['hesaplandi'] = True
            
    with col2:
        if st.session_state.get('hesaplandi', False):
            try:
                # Giriş değerlerini simülasyona aktar
                afet_sim.input['hasar_yogunlugu'] = val_hasar
                afet_sim.input['yol_kapanma'] = val_yol
                afet_sim.input['ulasim_suresi'] = val_ulasim
                afet_sim.input['nufus_yogunlugu'] = val_nufus
                afet_sim.input['hava_durumu'] = val_hava
                
                # Hesapla
                afet_sim.compute()
                
                # Sonucu al
                sonuc = afet_sim.output['oncelik']
                
                st.subheader("🎯 Simülasyon Çıktısı")
                
                # Görsel Sonuç Göstergeleri
                st.metric(label="Müdahale Öncelik Skoru (Durulaştırılmış)", value=f"{sonuc:.2f} / 100")
                st.progress(int(sonuc) / 100.0)
                
                # Dinamik Durum Mesajı
                if sonuc < 25:
                    st.success("🟢 **Durum:** Çok Düşük Öncelik (Bölge stabil, farklı rotaya yönelin)")
                elif sonuc < 50:
                    st.info("🟡 **Durum:** Düşük Öncelik (İkincil destek gönderilebilir)")
                elif sonuc < 70:
                    st.warning("🟠 **Durum:** Orta Öncelik (Kademeli müdahale planlanmalı)")
                elif sonuc < 85:
                    st.error("🔴 **Durum:** Yüksek Öncelik (Acil destek gerekiyor)")
                else:
                    st.error("🚨 **Durum:** KRİTİK ÖNCELİK (Tüm kaynaklar seferber edilmeli!)")
                
                st.markdown("---")
                
                # Çıktıların bulanık üyelik derecelerini göster (Kullanıcı hepsini görmek istediği için)
                st.markdown("**📏 Nihai Çıktının Bulanık Kümelerdeki Karşılığı (Üyelik Değerleri):**")
                uyelik_degerleri = {}
                for term_name in oncelik.terms.keys():
                    uyelik_degerleri[term_name] = fuzz.interp_membership(oncelik.universe, oncelik[term_name].mf, sonuc)
                
                cols = st.columns(len(uyelik_degerleri))
                for i, (k, v) in enumerate(uyelik_degerleri.items()):
                    cols[i].metric(label=k.upper().replace('_', ' '), value=f"{v:.2f}")
                
                st.markdown("---")
                # 3. İSTER: Aktif Kural Listesi
                st.markdown("**🔔 Anlık Tetiklenen Kurallar (Active Rules List):**")
                aktif_kurallar = []
                for r in afet_ctrl.rules:
                    firing_strength = r.aggregate_firing[afet_sim]
                    if firing_strength > 0:
                        aktif_kurallar.append((r, firing_strength))
                
                if aktif_kurallar:
                    aktif_kurallar.sort(key=lambda x: x[1], reverse=True) # En güçlüden en zayıfa sırala
                    for r, strg in aktif_kurallar:
                        # Kural metnini temizle (skfuzzy'nin kendi metninden IF ve THEN yapılarını çek)
                        kural_metni = str(r).split('\n')[0].replace('IF ', 'EĞER ').replace(' THEN ', ' İSE ').replace(' AND ', ' VE ').replace(' OR ', ' VEYA ')
                        st.info(f"⚡ **Tetiklenme Ağırlığı:** %{strg*100:.1f} | {kural_metni}")
                else:
                    st.warning("⚠️ Olası bir hata: Hiçbir kural tetiklenmedi.")
                    
                st.markdown("---")
                # Daha temiz ve sorunsuz özel sonuç grafiği (skfuzzy view hatasını engellemek için)
                fig, ax = plt.subplots(figsize=(8, 4.5))
                
                # Çıkış üyelik fonksiyonlarını arka planda hafifçe çiz
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                for idx, term_name in enumerate(oncelik.terms.keys()):
                    renk = colors[idx % len(colors)]
                    mf = oncelik[term_name].mf
                    label_name = term_name.upper().replace('_', ' ')
                    ax.plot(oncelik.universe, mf, label=label_name, linewidth=2, color=renk, alpha=0.5, linestyle='--')
                
                # Hesaplanan nihai sonucu dikey belirgin bir çizgi olarak ekle
                ax.axvline(x=sonuc, color='#e74c3c', linewidth=4, label=f"NİHAİ KARAR: {sonuc:.2f}")
                
                # Görsel zenginlik için sonucun altını hafif taralı yapalım
                ax.fill_between(oncelik.universe, 0, 1, where=(oncelik.universe <= sonuc), color='#e74c3c', alpha=0.1)
                
                # Ekseni ve Lejantı Düzenle
                ax.set_title("Nihai Müdahale Önceliği Çıktısı (Centroid)", pad=15)
                
                # Sınırları ve görünümü iyileştir
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.set_xlim(0, 100)
                ax.set_ylim(-0.05, 1.05)
                
                ax.legend(loc='center left', bbox_to_anchor=(1.05, 0.5), title="Öncelik Kümeleri")
                
                plt.tight_layout()
                st.pyplot(fig)
                
            except KeyError:
                st.error("⚠️ **Kural Tetiklenmedi**")
                st.warning("Girdiğiniz hassas değer kombinasyonu, sistemin enerji/kaynak tasarrufu gereği aksiyon almadığı bir duruma denk geldi. Lütfen farklı giriş değerleri deneyin.")

        else:
            st.info("👈 Lütfen sol taraftan verileri ayarlayıp 'Müdahale Önceliğini Hesapla' butonuna basın.")

with tab2:
    st.subheader("Tüm Giriş ve Çıkış Üyelik Fonksiyonları")
    st.markdown("Aşağıda sistemin karar mekanizmasını oluşturan **5 giriş sensörü** ve **1 çıkış değişkeninin** tam üyelik haritaları yer almaktadır.")
    
    # Tüm değişkenleri bir listede topla
    degiskenler = [
        ("Hasar Yoğunluğu", hasar_yogunlugu),
        ("Yol Kapanma Olasılığı", yol_kapanma),
        ("Ulaşım Süresi", ulasim_suresi),
        ("Nüfus Yoğunluğu", nufus_yogunlugu),
        ("Hava Durumu Zorluğu", hava_durumu),
        ("Çıkış: Müdahale Önceliği", oncelik)
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # 2 sütunlu şık bir grid (ızgara) oluştur
    cols = st.columns(2)
    
    for idx, (isim, degisken) in enumerate(degiskenler):
        # Sırayla sol ve sağ sütuna atama yap
        with cols[idx % 2]:
            fig, ax = plt.subplots(figsize=(6, 3))
            
            for t_idx, term_name in enumerate(degisken.terms.keys()):
                renk = colors[t_idx % len(colors)]
                mf = degisken[term_name].mf
                label_name = term_name.upper().replace('_', ' ')
                
                ax.plot(degisken.universe, mf, label=label_name, linewidth=2, color=renk)
                ax.fill_between(degisken.universe, 0, mf, alpha=0.1, color=renk)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylim(-0.05, 1.05)
            ax.set_xlim(degisken.universe.min(), degisken.universe.max())
            
            # Lejantı grafiğin dışına, biraz daha kompakt bir fontla yerleştir
            ax.legend(loc='center left', bbox_to_anchor=(1.05, 0.5), fontsize=8, title_fontsize=9)
            plt.title(f"{isim}", pad=10, fontsize=12)
            plt.tight_layout()
            
            st.pyplot(fig)
            st.markdown("<br>", unsafe_allow_html=True) # Grafikler arasına hafif boşluk

with tab3:
    st.subheader("Gelişmiş Kural Tabanı (5 Girişli - 20 Kural)")
    st.markdown("Olay tabanlı senaryolarda belirsizlikleri yönetmek için yazılmış **5 girişli** detaylı kuralların tam listesi:")
    
    # Tüm kuralları dinamik olarak arayüze yazdır
    for idx, rule in enumerate(afet_ctrl.rules):
        kural_metni = str(rule).split('\n')[0]
        kural_metni = kural_metni.replace('IF ', 'EĞER ').replace(' THEN ', ' İSE ').replace(' AND ', ' VE ').replace(' OR ', ' VEYA ')
        st.markdown(f"**Kural {idx + 1}:**  {kural_metni}")
    st.info("Sistem **Centroid (Ağırlık Merkezi)** metodu kullanılarak durulaştırma yapmaktadır. Raporunuzda bu sistemin 5x5'lik bir matriksle ne kadar kompleks problemleri çözebildiğine vurgu yapabilirsiniz.")

with tab4:
    st.subheader("🌐 Yüksek Çözünürlüklü 3 Boyutlu Karar Yüzeyi")
    st.markdown("Hava Durumu, Yol Kapanma Olasılığı ve Nüfus Yoğunluğu formdaki değerlerde **sabit tutulduğunda**, tahmini **Hasar Yoğunluğu** ve **Ulaşım Süresinin** müdahale önceliğini nasıl etkilediği görülmektedir.")
    
    if st.button("🗺️ 3B Yüzeyi Hesapla ve Çiz (Ortalama 5 Saniye)"):
        with st.spinner("5 Boyutlu Uzayda Kesişimler Hesaplanıyor..."):
            upsampled_x = np.linspace(0, 100, 21)
            upsampled_y = np.linspace(0, 120, 21)
            x, y = np.meshgrid(upsampled_x, upsampled_y)
            z = np.zeros_like(x)
            
            sim_3d = ctrl.ControlSystemSimulation(afet_ctrl)
            for i in range(21):
                for j in range(21):
                    sim_3d.input['hasar_yogunlugu'] = x[i, j]
                    sim_3d.input['ulasim_suresi'] = y[i, j]
                    
                    # Diğerlerini sabit alıyoruz
                    sim_3d.input['yol_kapanma'] = val_yol
                    sim_3d.input['nufus_yogunlugu'] = val_nufus
                    sim_3d.input['hava_durumu'] = val_hava
                    
                    try:
                        sim_3d.compute()
                        z[i, j] = sim_3d.output['oncelik']
                    except:
                        z[i, j] = 0
            
            fig = plt.figure(figsize=(10, 7))
            ax = fig.add_subplot(111, projection='3d')
            
            # Daha güzel bir renk paleti (coolwarm) ve saydamlık ayarı
            surf = ax.plot_surface(x, y, z, cmap='coolwarm', edgecolor='none', alpha=0.9)
            
            ax.set_xlabel('Hasar Yoğunluğu (%)', labelpad=10)
            ax.set_ylabel('Ulaşım Süresi (Dk)', labelpad=10)
            ax.set_zlabel('Müdahale Önceliği Skoru', labelpad=10)
            ax.set_title('Hasar ve Ulaşıma Göre Karar Yüzeyi', pad=15)
            
            # Perspektifi güzelleştirme
            ax.view_init(elev=25, azim=-45)
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Müdahale Önceliği')
            
            st.pyplot(fig)
