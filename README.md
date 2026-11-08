# 🖼️ Multimodal Image Classifier

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.0-black?logo=flask&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.2.0-EE4C2C?logo=pytorch&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Transformers-FFD21E?logo=huggingface&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green)

**Multimodal Image Classifier**, Hugging Face üzerindeki açık kaynaklı **Görsel-Dil Modellerini (Vision-Language / Multimodal Models)** kullanarak **sıfır eğitimle (Zero-Shot)** toplu görüntü sınıflandırması yapan, model tahminlerini gerçek etiketlerle (**Ground Truth**) kıyaslayarak kapsamlı performans metrikleri (**Accuracy, Precision, Recall, F1-Score, Confusion Matrix**) üreten ve farklı modelleri yan yana karşılaştıran uçtan uca bir web uygulamasıdır.

---

## 🎯 Temel Özellikler

- 🤖 **Hugging Face Model Entegrasyonu**: CLIP, BLIP, GIT, ViLT, Qwen-VL gibi farklı mimarilerdeki açık kaynak modelleri API anahtarı ile doğrudan arayüzden indirme ve yerel önbellekte yönetme.
- 📂 **Sıfır Eğitimle (Zero-Shot) Toplu Sınıflandırma**: Modeli yeniden eğitmeye gerek kalmadan, çalışma anında tanımlanan özel sınıflara (örn. *kedi, köpek, tavşan*) göre bir klasördeki yüzlerce görüntüyü arka planda asenkron olarak sınıflandırma.
- 📊 **Kapsamlı Performans Değerlendirmesi**: Tahmin sonuçlarını Ground Truth JSON dosyası ile eşleştirerek genel ve sınıf bazlı (per-class) **Accuracy**, **Precision**, **Recall** ve **F1-Score** hesaplama.
- 🎨 **Hata Matrisi (Confusion Matrix)**: Hem web arayüzünde interaktif tablo olarak hem de yüksek çözünürlüklü `.png` ısı haritası (heatmap) olarak kaydetme.
- ⚖️ **Çoklu Model Karşılaştırma**: Farklı modellerin veya farklı zamanlarda yapılan testlerin sonuçlarını sıralanabilir tabloda yan yana kıyaslama.
- 🛡️ **Gelişmiş Doğrulama ve Hata Yönetimi**: Hem istemci (Frontend) hem sunucu (Backend) tarafında kapsamlı girdi doğrulama, otomatik yeniden deneme (exponential backoff retry) ve GPU'dan CPU'ya otomatik geçiş (fallback) desteği.

---

## 🏗️ Sistem Mimarisi ve Proje Yapısı

```text
DATA_CLASSIFICATION/
├── backend/                        # Python Flask REST API & İş Mantığı
│   ├── app.py                      # API Endpoint'leri ve Asenkron Görev Yönetimi
│   ├── model_manager.py            # Hugging Face Model İndirme ve Çoklu Strateji Yükleyici
│   ├── classification_service.py   # CLIP, ViLT ve Vision2Seq Sınıflandırma Motoru
│   ├── evaluation_service.py       # Metrik Hesaplama ve Confusion Matrix Görselleştirme
│   ├── storage_manager.py          # Dosya Sistemi ve JSON Veri Kalıcılığı Yönetimi
│   ├── validators.py               # Girdi Doğrulama (Validation) Kuralları
│   ├── exceptions.py               # Özel HTTP Hata Sınıfları
│   ├── config.py                   # Geliştirme Ortamı Konfigürasyonu
│   ├── config_production.py        # Üretim (Production) Ortamı Konfigürasyonu
│   ├── create_metadata.py          # Manuel Eklenen Modeller İçin Metadata Oluşturucu
│   └── tests/                      # Pytest Birim ve Entegrasyon Testleri
├── frontend/                       # Vanilla JS (ES6+), HTML5, CSS3 Web Arayüzü
│   ├── index.html                  # Ana Karşılama ve Navigasyon Sayfası
│   ├── pages/
│   │   ├── model-selection.html    # Model İndirme ve Listeleme Sayfası
│   │   ├── classification.html     # Klasör Seçimi, Sınıf Tanımlama ve Sınıflandırma
│   │   ├── evaluation.html         # Ground Truth Yükleme ve Metrik Analizi
│   │   └── comparison.html         # Modeller Arası Performans Karşılaştırma
│   ├── css/
│   │   ├── main.css                # Temel Tasarım Sistemi ve Değişkenler
│   │   └── components.css          # Kart, Tablo, Form, Progress Bar Bileşenleri
│   └── js/
│       ├── api.js                  # Merkezi Fetch Wrapper, Retry Mekanizması ve Validator'lar
│       ├── model-selection.js      # Model Seçim Sayfası Mantığı
│       ├── classification.js       # Sınıflandırma ve Polling Mantığı
│       ├── evaluation.js           # Değerlendirme ve Rapor İndirme Mantığı
│       └── comparison.js           # Karşılaştırma ve Tablo Sıralama Mantığı
├── data/                           # Veri ve Çıktı Dizini
│   ├── models/                     # İndirilen Hugging Face Modelleri
│   ├── predictions/                # Üretilen Tahmin JSON Dosyaları
│   ├── results/                    # Değerlendirme Metrikleri ve Confusion Matrix Görselleri
│   ├── temp/                       # Geçici Dosyalar
│   └── example_ground_truth.json   # Örnek Gerçek Etiket (Ground Truth) Dosyası
├── requirements.txt                # Python Paket Bağımlılıkları
├── .env.example                    # Örnek Ortam Değişkenleri Şablonu
├── API_DOCUMENTATION.md            # Detaylı REST API Dokümantasyonu
└── DEPLOYMENT.md                   # Production Kurulum Rehberi
```

---

## ⚙️ Kurulum

### 1. Gereksinimler
- **Python**: 3.8 veya üzeri
- **RAM**: Minimum 8 GB (Büyük modeller için 16 GB+ önerilir)
- **GPU (Opsiyonel)**: CUDA destekli NVIDIA GPU (varsa otomatik olarak `float16` / `float32` ile kullanılır, yoksa CPU'da çalışır)

### 2. Projeyi Klonlayın ve Sanal Ortam Oluşturun

```bash
git clone <repository-url>
cd DATA_CLASSIFICATION

# Windows için sanal ortam:
python -m venv venv
venv\Scripts\activate

# Linux / macOS için sanal ortam:
python3 -m venv venv
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

---

## 🚀 Çalıştırma

### 1. Backend Sunucusunu Başlatın

Proje kök dizinindeyken:

```bash
python -m backend.app
```
Backend API sunucusu varsayılan olarak `http://127.0.0.1:5000` adresinde çalışacaktır.

### 2. Frontend Arayüzünü Başlatın

Yeni bir terminal açıp `frontend` klasöründe basit bir HTTP sunucusu başlatın:

```bash
cd frontend
python -m http.server 8000
```
Tarayıcınızdan `http://localhost:8000` adresine giderek uygulamayı kullanmaya başlayabilirsiniz.

---

## 📖 Adım Adım Kullanım Rehberi

### Adım 1: Model Seçimi ve İndirme (`Model Selection`)
1. [Hugging Face Token Ayarları](https://huggingface.co/settings/tokens) sayfasından `hf_` ile başlayan bir erişim anahtarı (Access Token) alın.
2. **Model Selection** sayfasında API anahtarınızı ve model adını (`organizasyon/model-adı` formatında) girin.
   - **Örnek Modeller**:
     - `openai/clip-vit-base-patch32` *(Zero-Shot CLIP Sınıflandırma)*
     - `Salesforce/blip-image-captioning-base` *(Vision-to-Seq Altyazılama & Eşleştirme)*
     - `dandelin/vilt-b32-finetuned-vqa` *(Görsel Soru-Cevap / VQA)*
     - `microsoft/git-base`
3. **Download Model** butonuna tıklayın. İndirilen modeller `data/models/` altına kaydedilir ve tekrar indirilmesine gerek kalmaz.

### Adım 2: Görüntü Sınıflandırma (`Classification`)
1. **Classification** sayfasında indirdiğiniz modeli seçin.
2. Sınıflandırmak istediğiniz görüntülerin bulunduğu yerel klasör yolunu (örn. `C:\Users\Kullanici\Pictures\hayvanlar`) girip **Validate Folder** butonuna tıklayın.
3. Sınıf sayısını girin ve sınıf isimlerini (örn. `cat`, `dog`, `rabbit`) tanımlayın.
4. **Start Classification** butonuna basın. İşlem arka planda çalışırken ilerleme çubuğundan durumu takip edebilirsiniz. Tamamlandığında tahminler `data/predictions/` klasörüne JSON olarak kaydedilir.

### Adım 3: Performans Değerlendirme (`Evaluation`)
1. Gerçek etiketleri içeren **Ground Truth JSON** dosyanızı hazırlayın (Örnek: `data/example_ground_truth.json`):
   ```json
   {
     "cat_001.jpg": "kedi",
     "dog_001.jpg": "köpek",
     "rabbit_001.jpg": "tavşan"
   }
   ```
2. **Evaluation** sayfasında **Ground Truth JSON** dosyasını ve `data/predictions/` altında oluşan **Prediction JSON** dosyasını yükleyin.
3. **Evaluate Model** butonuna tıklayın.
4. **Accuracy, Precision, Recall, F1-Score**, sınıf bazlı metrikler ve **Confusion Matrix** ekranda gösterilir ve sonuçlar otomatik olarak `data/results/<model_adi>/<tarih>/` dizinine kaydedilir.

### Adım 4: Model Karşılaştırma (`Comparison`)
1. **Comparison** sayfasına gidin.
2. Daha önce değerlendirilmiş modeller arasından en az 2 sonucu seçip **Compare Selected Results** butonuna tıklayın.
3. Tablo başlıklarına tıklayarak modelleri doğruluk (Accuracy) veya F1-Score değerlerine göre sıralayın.

---

## 🔌 REST API Özeti

| Metot | Endpoint | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Sunucu sağlık kontrolü |
| `POST` | `/api/download-model` | Hugging Face üzerinden yeni model indirir |
| `GET` | `/api/models` | İndirilmiş yerel modelleri listeler |
| `POST` | `/api/classify` | Klasördeki görüntüler için asenkron sınıflandırma başlatır |
| `GET` | `/api/classification-status/<id>` | Devam eden sınıflandırma görevinin ilerlemesini döndürür |
| `GET` | `/api/predictions` | Kaydedilmiş tahmin dosyalarını listeler |
| `POST` | `/api/upload-ground-truth` | Ground truth JSON dosyasını yükler ve doğrular |
| `POST` | `/api/evaluate` | Kayıtlı `prediction_id` ve `ground_truth_path` ile değerlendirme yapar |
| `POST` | `/api/evaluate-direct` | Doğrudan gönderilen tahmin ve ground truth JSON verilerini değerlendirir |
| `GET` | `/api/results` | Tüm geçmiş değerlendirme sonuçlarını listeler |
| `GET` | `/api/result/<result_id>` | Belirli bir değerlendirme sonucunun detaylarını getirir |
| `POST` | `/api/compare` | Seçilen birden fazla değerlendirme sonucunu yan yana karşılaştırır |

Detaylı istek/yanıt örnekleri için [API_DOCUMENTATION.md](API_DOCUMENTATION.md) dosyasına göz atabilirsiniz.

---

## 🧪 Testler

Backend birim ve entegrasyon testlerini çalıştırmak için:

```bash
pip install -r backend/tests/requirements-test.txt
pytest -v
```

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır.
