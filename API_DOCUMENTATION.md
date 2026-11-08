# API Documentation

Bu dokümantasyon, Multimodal Image Classifier backend REST API'sinin detaylı açıklamasını içerir.

## Base URL

```
http://127.0.0.1:5000
```

Production ortamında domain adınızı kullanın.

## İçindekiler

- [Authentication](#authentication)
- [Model Management](#model-management)
- [Classification](#classification)
- [Evaluation](#evaluation)
- [Results & Comparison](#results--comparison)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Authentication

API, Hugging Face API anahtarı kullanır. Anahtar sadece model indirme endpoint'inde gereklidir ve request body'de gönderilir.

## Model Management

### Download Model

Hugging Face'den model indirir.

**Endpoint**: `POST /api/download-model`

**Request Body**:
```json
{
  "api_key": "hf_xxxxxxxxxxxxxxxxxxxxx",
  "model_name": "Salesforce/blip-image-captioning-base"
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key | string | Yes | Hugging Face API token (min 10 karakter) |
| model_name | string | Yes | Model adı (organization/model-name formatı) |

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Model başarıyla indirildi",
  "model_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_name": "Salesforce/blip-image-captioning-base",
  "download_date": "2025-11-13T10:30:00"
}
```

**Error Responses**:

*400 Bad Request* - Geçersiz input:
```json
{
  "error": "Validation error",
  "details": {
    "api_key": "API key en az 10 karakter olmalıdır",
    "model_name": "Model adı 'organization/model-name' formatında olmalıdır"
  }
}
```

*401 Unauthorized* - Geçersiz API key:
```json
{
  "error": "Authentication failed",
  "message": "Geçersiz API key"
}
```

*404 Not Found* - Model bulunamadı:
```json
{
  "error": "Model not found",
  "message": "Belirtilen model Hugging Face'de bulunamadı"
}
```

*500 Internal Server Error* - Sunucu hatası:
```json
{
  "error": "Download failed",
  "message": "Model indirme sırasında bir hata oluştu"
}
```

---

### List Models

İndirilen tüm modelleri listeler.

**Endpoint**: `GET /api/models`

**Request**: Parametre gerektirmez

**Success Response** (200 OK):
```json
{
  "success": true,
  "models": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Salesforce/blip-image-captioning-base",
      "download_date": "2025-11-13T10:30:00",
      "path": "data/models/550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "microsoft/git-base",
      "download_date": "2025-11-12T15:20:00",
      "path": "data/models/660e8400-e29b-41d4-a716-446655440001"
    }
  ],
  "count": 2
}
```

**Error Response**:

*500 Internal Server Error*:
```json
{
  "error": "Failed to list models",
  "message": "Model listesi alınamadı"
}
```

---

## Classification

### Start Classification

Belirtilen klasördeki görüntüleri sınıflandırır.

**Endpoint**: `POST /api/classify`

**Request Body**:
```json
{
  "model_id": "550e8400-e29b-41d4-a716-446655440000",
  "folder_path": "C:/Users/user/images/animals",
  "classes": ["kedi", "köpek", "tavşan"]
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | İndirilen modelin UUID'si |
| folder_path | string | Yes | Görüntülerin bulunduğu klasör yolu |
| classes | array[string] | Yes | Sınıf isimleri (2-50 arası, benzersiz) |

**Success Response** (202 Accepted):
```json
{
  "success": true,
  "message": "Sınıflandırma başlatıldı",
  "prediction_id": "770e8400-e29b-41d4-a716-446655440002",
  "total_images": 150,
  "status": "processing"
}
```

**Error Responses**:

*400 Bad Request* - Validasyon hatası:
```json
{
  "error": "Validation error",
  "details": {
    "classes": "En az 2, en fazla 50 sınıf tanımlanmalıdır",
    "folder_path": "Klasör bulunamadı veya okunamıyor"
  }
}
```

*404 Not Found* - Model bulunamadı:
```json
{
  "error": "Model not found",
  "message": "Belirtilen model ID'si bulunamadı"
}
```

---

### Get Classification Status

Sınıflandırma işleminin durumunu sorgular.

**Endpoint**: `GET /api/classification-status/{prediction_id}`

**URL Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| prediction_id | string | Sınıflandırma işleminin UUID'si |

**Success Response** (200 OK):

*İşlem devam ediyor*:
```json
{
  "success": true,
  "prediction_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "processing",
  "progress": 45.5,
  "current": 68,
  "total": 150,
  "message": "Sınıflandırma devam ediyor..."
}
```

*İşlem tamamlandı*:
```json
{
  "success": true,
  "prediction_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "completed",
  "progress": 100,
  "current": 150,
  "total": 150,
  "message": "Sınıflandırma tamamlandı",
  "results_path": "data/predictions/770e8400-e29b-41d4-a716-446655440002.json"
}
```

*İşlem başarısız*:
```json
{
  "success": false,
  "prediction_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "failed",
  "error": "Model yükleme hatası",
  "message": "Sınıflandırma başarısız oldu"
}
```

**Error Response**:

*404 Not Found*:
```json
{
  "error": "Prediction not found",
  "message": "Belirtilen prediction ID'si bulunamadı"
}
```

---

## Evaluation

### Upload Ground Truth

Ground truth dosyasını yükler.

**Endpoint**: `POST /api/upload-ground-truth`

**Request**: `multipart/form-data`

**Form Data**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | JSON formatında ground truth dosyası (max 10MB) |

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Ground truth başarıyla yüklendi",
  "ground_truth_id": "880e8400-e29b-41d4-a716-446655440003",
  "file_name": "ground_truth.json",
  "entries_count": 150
}
```

**Error Responses**:

*400 Bad Request* - Geçersiz dosya:
```json
{
  "error": "Invalid file",
  "message": "Dosya JSON formatında olmalıdır"
}
```

*413 Payload Too Large*:
```json
{
  "error": "File too large",
  "message": "Dosya boyutu 10MB'ı aşamaz"
}
```

---

### Evaluate Model

Model performansını değerlendirir.

**Endpoint**: `POST /api/evaluate`

**Request Body**:
```json
{
  "prediction_id": "770e8400-e29b-41d4-a716-446655440002",
  "ground_truth_id": "880e8400-e29b-41d4-a716-446655440003"
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| prediction_id | string | Yes | Sınıflandırma sonucu UUID'si |
| ground_truth_id | string | Yes | Ground truth dosyası UUID'si |

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Değerlendirme tamamlandı",
  "result_id": "990e8400-e29b-41d4-a716-446655440004",
  "metrics": {
    "accuracy": 0.9533,
    "precision": 0.9487,
    "recall": 0.9467,
    "f1_score": 0.9477,
    "per_class_metrics": {
      "kedi": {
        "precision": 0.96,
        "recall": 0.94,
        "f1_score": 0.95,
        "support": 50
      },
      "köpek": {
        "precision": 0.93,
        "recall": 0.95,
        "f1_score": 0.94,
        "support": 50
      },
      "tavşan": {
        "precision": 0.96,
        "recall": 0.95,
        "f1_score": 0.955,
        "support": 50
      }
    }
  },
  "confusion_matrix": [
    [47, 2, 1],
    [1, 48, 1],
    [2, 1, 47]
  ],
  "classes": ["kedi", "köpek", "tavşan"],
  "confusion_matrix_image": "data/results/blip-base/2025-11-13_10-45-30/confusion_matrix.png"
}
```

**Error Responses**:

*400 Bad Request* - Veri eşleşmiyor:
```json
{
  "error": "Data mismatch",
  "message": "Ground truth ve prediction dosyaları eşleşmiyor",
  "details": {
    "missing_in_predictions": ["image5.jpg", "image6.jpg"],
    "missing_in_ground_truth": ["image7.jpg"]
  }
}
```

*404 Not Found*:
```json
{
  "error": "Not found",
  "message": "Prediction veya ground truth bulunamadı"
}
```

---

## Results & Comparison

### List Results

Tüm değerlendirme sonuçlarını listeler.

**Endpoint**: `GET /api/results`

**Query Parameters** (Opsiyonel):
| Parameter | Type | Description |
|-----------|------|-------------|
| model_name | string | Model adına göre filtrele |
| limit | integer | Sonuç sayısı limiti (default: 100) |
| offset | integer | Sayfalama için offset (default: 0) |

**Success Response** (200 OK):
```json
{
  "success": true,
  "results": [
    {
      "result_id": "990e8400-e29b-41d4-a716-446655440004",
      "model_name": "Salesforce/blip-image-captioning-base",
      "date": "2025-11-13_10-45-30",
      "metrics": {
        "accuracy": 0.9533,
        "precision": 0.9487,
        "recall": 0.9467,
        "f1_score": 0.9477
      }
    },
    {
      "result_id": "aa0e8400-e29b-41d4-a716-446655440005",
      "model_name": "microsoft/git-base",
      "date": "2025-11-12_15-30-00",
      "metrics": {
        "accuracy": 0.9267,
        "precision": 0.9201,
        "recall": 0.9233,
        "f1_score": 0.9217
      }
    }
  ],
  "count": 2,
  "total": 2
}
```

---

### Get Result

Belirli bir değerlendirme sonucunu getirir.

**Endpoint**: `GET /api/result/{result_id}`

**URL Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| result_id | string | Sonuç UUID'si |

**Success Response** (200 OK):
```json
{
  "success": true,
  "result_id": "990e8400-e29b-41d4-a716-446655440004",
  "model_name": "Salesforce/blip-image-captioning-base",
  "date": "2025-11-13_10-45-30",
  "metrics": {
    "accuracy": 0.9533,
    "precision": 0.9487,
    "recall": 0.9467,
    "f1_score": 0.9477,
    "per_class_metrics": {
      "kedi": {
        "precision": 0.96,
        "recall": 0.94,
        "f1_score": 0.95,
        "support": 50
      }
    }
  },
  "confusion_matrix": [[47, 2, 1], [1, 48, 1], [2, 1, 47]],
  "classes": ["kedi", "köpek", "tavşan"],
  "confusion_matrix_image": "data/results/blip-base/2025-11-13_10-45-30/confusion_matrix.png"
}
```

**Error Response**:

*404 Not Found*:
```json
{
  "error": "Result not found",
  "message": "Belirtilen result ID'si bulunamadı"
}
```

---

### Compare Models

Birden fazla modelin performansını karşılaştırır.

**Endpoint**: `POST /api/compare`

**Request Body**:
```json
{
  "result_ids": [
    "990e8400-e29b-41d4-a716-446655440004",
    "aa0e8400-e29b-41d4-a716-446655440005"
  ]
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| result_ids | array[string] | Yes | Karşılaştırılacak sonuç UUID'leri (min 2) |

**Success Response** (200 OK):
```json
{
  "success": true,
  "comparison": [
    {
      "result_id": "990e8400-e29b-41d4-a716-446655440004",
      "model_name": "Salesforce/blip-image-captioning-base",
      "date": "2025-11-13_10-45-30",
      "metrics": {
        "accuracy": 0.9533,
        "precision": 0.9487,
        "recall": 0.9467,
        "f1_score": 0.9477
      }
    },
    {
      "result_id": "aa0e8400-e29b-41d4-a716-446655440005",
      "model_name": "microsoft/git-base",
      "date": "2025-11-12_15-30-00",
      "metrics": {
        "accuracy": 0.9267,
        "precision": 0.9201,
        "recall": 0.9233,
        "f1_score": 0.9217
      }
    }
  ],
  "best_model": {
    "metric": "accuracy",
    "result_id": "990e8400-e29b-41d4-a716-446655440004",
    "model_name": "Salesforce/blip-image-captioning-base",
    "value": 0.9533
  }
}
```

**Error Responses**:

*400 Bad Request*:
```json
{
  "error": "Invalid request",
  "message": "En az 2 sonuç seçilmelidir"
}
```

*404 Not Found*:
```json
{
  "error": "Results not found",
  "message": "Bazı sonuçlar bulunamadı",
  "missing_ids": ["aa0e8400-e29b-41d4-a716-446655440005"]
}
```

---

## Error Handling

Tüm API endpoint'leri tutarlı hata formatı kullanır.

### Error Response Format

```json
{
  "error": "Error type",
  "message": "Kullanıcı dostu hata mesajı",
  "details": {
    "field_name": "Detaylı hata açıklaması"
  },
  "timestamp": "2025-11-13T10:45:30",
  "path": "/api/classify"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | İstek başarılı |
| 201 | Created | Kaynak oluşturuldu |
| 202 | Accepted | İstek kabul edildi (async işlem) |
| 400 | Bad Request | Geçersiz istek parametreleri |
| 401 | Unauthorized | Kimlik doğrulama başarısız |
| 403 | Forbidden | Erişim izni yok |
| 404 | Not Found | Kaynak bulunamadı |
| 413 | Payload Too Large | Dosya çok büyük |
| 422 | Unprocessable Entity | Validasyon hatası |
| 429 | Too Many Requests | Rate limit aşıldı |
| 500 | Internal Server Error | Sunucu hatası |
| 503 | Service Unavailable | Servis geçici olarak kullanılamıyor |

### Common Error Types

**ValidationError**: Input validasyon hatası
```json
{
  "error": "ValidationError",
  "message": "Girdi doğrulama hatası",
  "details": {
    "field": "Hata açıklaması"
  }
}
```

**AuthenticationError**: Kimlik doğrulama hatası
```json
{
  "error": "AuthenticationError",
  "message": "Geçersiz API key"
}
```

**ModelNotFoundError**: Model bulunamadı
```json
{
  "error": "ModelNotFoundError",
  "message": "Model bulunamadı"
}
```

**FileNotFoundError**: Dosya bulunamadı
```json
{
  "error": "FileNotFoundError",
  "message": "Belirtilen dosya bulunamadı"
}
```

**ProcessingError**: İşlem hatası
```json
{
  "error": "ProcessingError",
  "message": "İşlem sırasında bir hata oluştu"
}
```

---

## Rate Limiting

API, rate limiting kullanır (production ortamında):

- **Limit**: 100 istek / dakika / IP
- **Model İndirme**: 5 istek / saat / IP
- **Sınıflandırma**: 10 istek / saat / IP

Rate limit aşıldığında:

**Response** (429 Too Many Requests):
```json
{
  "error": "Rate limit exceeded",
  "message": "Çok fazla istek gönderildi",
  "retry_after": 60,
  "limit": 100,
  "remaining": 0,
  "reset": "2025-11-13T11:00:00"
}
```

**Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699876800
Retry-After: 60
```

---

## Request Examples

### cURL Examples

**Model İndirme**:
```bash
curl -X POST http://127.0.0.1:5000/api/download-model \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "hf_xxxxxxxxxxxxxxxxxxxxx",
    "model_name": "Salesforce/blip-image-captioning-base"
  }'
```

**Sınıflandırma Başlatma**:
```bash
curl -X POST http://127.0.0.1:5000/api/classify \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "550e8400-e29b-41d4-a716-446655440000",
    "folder_path": "C:/Users/user/images",
    "classes": ["kedi", "köpek", "tavşan"]
  }'
```

**Ground Truth Yükleme**:
```bash
curl -X POST http://127.0.0.1:5000/api/upload-ground-truth \
  -F "file=@ground_truth.json"
```

### JavaScript (Fetch) Examples

**Model İndirme**:
```javascript
const response = await fetch('http://127.0.0.1:5000/api/download-model', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    api_key: 'hf_xxxxxxxxxxxxxxxxxxxxx',
    model_name: 'Salesforce/blip-image-captioning-base'
  })
});

const data = await response.json();
console.log(data);
```

**Sonuçları Listeleme**:
```javascript
const response = await fetch('http://127.0.0.1:5000/api/results');
const data = await response.json();
console.log(data.results);
```

### Python (requests) Examples

**Model İndirme**:
```python
import requests

response = requests.post(
    'http://127.0.0.1:5000/api/download-model',
    json={
        'api_key': 'hf_xxxxxxxxxxxxxxxxxxxxx',
        'model_name': 'Salesforce/blip-image-captioning-base'
    }
)

data = response.json()
print(data)
```

**Değerlendirme**:
```python
import requests

response = requests.post(
    'http://127.0.0.1:5000/api/evaluate',
    json={
        'prediction_id': '770e8400-e29b-41d4-a716-446655440002',
        'ground_truth_id': '880e8400-e29b-41d4-a716-446655440003'
    }
)

data = response.json()
print(f"Accuracy: {data['metrics']['accuracy']}")
print(f"F1-Score: {data['metrics']['f1_score']}")
```

---

## Versioning

API versiyonu: **v1**

Gelecekte API değişiklikleri için versiyonlama kullanılacaktır:
- `/api/v1/...`
- `/api/v2/...`

Şu anda tüm endpoint'ler `/api/` prefix'i kullanır.

---

## Support

API ile ilgili sorularınız için:
- GitHub Issues: Proje repository'sinde issue açın
- Documentation: README.md dosyasına bakın

---

## Changelog

### v1.0.0 (2025-11-13)
- İlk API release
- Model management endpoint'leri
- Classification endpoint'leri
- Evaluation endpoint'leri
- Results & comparison endpoint'leri
