# Backend Tests

Bu dizin, backend bileşenleri için unit testleri içerir.

## Test Dosyaları

- `conftest.py` - Pytest konfigürasyonu ve paylaşılan fixture'lar
- `test_storage_manager.py` - StorageManager için testler
- `test_model_manager.py` - ModelManager için testler
- `test_classification_service.py` - ClassificationService için testler
- `test_evaluation_service.py` - EvaluationService için testler
- `test_api_endpoints.py` - Flask API endpoint'leri için testler

## Kurulum

Test bağımlılıklarını yükleyin:

```bash
pip install -r requirements-test.txt
```

## Testleri Çalıştırma

Tüm testleri çalıştırmak için:

```bash
pytest backend/tests/
```

Belirli bir test dosyasını çalıştırmak için:

```bash
pytest backend/tests/test_storage_manager.py
```

Verbose çıktı ile:

```bash
pytest backend/tests/ -v
```

Test coverage raporu ile:

```bash
pytest backend/tests/ --cov=backend --cov-report=html
```

## Test Yapısı

Testler, her backend bileşeni için ayrı dosyalarda organize edilmiştir:

- **Storage Manager Tests**: JSON okuma/yazma, dizin yönetimi, sonuç listeleme
- **Model Manager Tests**: Model indirme, metadata yönetimi, API key doğrulama
- **Classification Service Tests**: Görüntü yükleme, sınıflandırma, tahmin kaydetme
- **Evaluation Service Tests**: Metrik hesaplama, confusion matrix, sonuç kaydetme
- **API Endpoint Tests**: HTTP endpoint'leri, hata yönetimi, request/response doğrulama

## Fixture'lar

`conftest.py` dosyası, testler arasında paylaşılan fixture'ları içerir:

- `temp_dir` - Geçici test dizini
- `sample_image` - Test için örnek görüntü
- `sample_images` - Birden fazla test görüntüsü
- `sample_ground_truth` - Örnek ground truth JSON dosyası
- `sample_predictions` - Örnek tahmin verileri
- `sample_classes` - Örnek sınıf isimleri
- `mock_model_metadata` - Mock model metadata
- `mock_prediction_data` - Mock tahmin verileri

## Not

Testler, gerçek model indirme ve inference işlemlerini mock'lar. Bu, testlerin hızlı çalışmasını ve dış bağımlılıklara ihtiyaç duymamasını sağlar.
