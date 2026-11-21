# G3.4 – Kiểm chứng môi trường và tính toàn vẹn của thí nghiệm

**Dự án:** Reference-Free Critical Error Detection trên WMT 2020 MQM English→German
**Giai đoạn:** G3 – Reproducibility and Evidence
**Trạng thái:** Hoàn thành các kiểm tra đã xác định cho G3.4
**Ngày ghi nhận:** 2026-11-04

## 1. Mục tiêu

G3.4 kiểm tra các bằng chứng kỹ thuật cần thiết để xác định môi trường thực thi, truy xuất dữ liệu đầu vào và xác nhận tính nhất quán của phép chia Train/Dev/Test được sử dụng trong thí nghiệm.

Phạm vi gồm:
- Môi trường Python và các thư viện phụ thuộc.
- Tính nhất quán giữa tệp dữ liệu có gán split và snapshot.
- Tính nhất quán giữa snapshot và ba tệp Train/Dev/Test mà các script thực nghiệm sử dụng.
- Các thông số split và thống kê trong manifest.

## 2. Môi trường thực thi

| Thành phần | Giá trị |
|---|---|
| Hệ điều hành | Windows |
| Python | 3.13.18 |
| Môi trường ảo | `.venv_mla` |
| Python executable | `.\.venv_mla\python.exe` |
| scikit-learn | 1.9.1 |
| pandas | 3.1.0 |
| numpy | 2.5.4 |
| scipy | 1.18.1 |

Danh sách thư viện đã cài được lưu trong `requirements.txt`, tạo từ kết quả `pip freeze`.

SHA-256 của `requirements.txt` tại thời điểm ghi nhận:

```text
A6B946F0B69D5AB095FEB419E6F0EE1EBD6CD0FDCC45FC0D2568C665F54922F8
```

Môi trường `.venv_mla` được sử dụng cho dự án. Môi trường `.venv` cũ không được dùng do gặp lỗi môi trường Python.

## 3. Kiểm chứng snapshot và SHA-256

Manifest tại `results/week10/locked_split/manifest.json` ghi nhận:

- Phương pháp chia: `GroupShuffleSplit by doc`.
- Random state lần chia thứ nhất: `42`.
- Random state lần chia thứ hai: `43`.
- Tỷ lệ mục tiêu: Train 70%, Dev 15%, Test 15%.
- Tổng số mẫu: 9.926.
- Tổng số documents: 130.
- Tổng số mẫu Critical: 1.183.
- Số documents giao nhau giữa từng cặp split: 0.

SHA-256 được kiểm tra trực tiếp bằng PowerShell cho hai tệp:

- `results/week10/model_data/segments_with_fixed_splits.csv`
- `results/week10/locked_split/segments_week10_90_20_20.csv`

Cả hai tệp có cùng SHA-256:

```text
780CD9F0B2B32042AD95F98E67318C03814FBE895E1F0EF8755DA847E8D287AB
```

Giá trị này khớp với `source_sha256` và `snapshot_sha256` trong manifest. Tại thời điểm kiểm tra, tệp nguồn và snapshot có nội dung nhị phân giống nhau theo kiểm tra SHA-256.

## 4. Đối chiếu Train/Dev/Test với snapshot

Snapshot có 9.926 dòng và 11 cột, trong đó cột `split` xác định tập dữ liệu của mỗi bản ghi.

Mỗi tập được trích từ snapshot bằng cách lọc theo `split`, loại bỏ cột `split`, rồi đối chiếu với tệp tương ứng trong `results/week10/model_data/`.

| Tiêu chí | Train | Dev | Test |
|---|---:|---:|---:|
| Số mẫu kỳ vọng từ snapshot | 6.797 | 1.554 | 1.575 |
| Số mẫu trong tệp thực tế | 6.797 | 1.554 | 1.575 |
| Danh sách cột giống nhau | Có | Có | Có |
| Nội dung và thứ tự dòng giống nhau (`DataFrame.equals`) | Có | Có | Có |
| Số documents | 90 | 20 | 20 |
| Số nhãn Critical (`y_primary = 1`) | 803 | 218 | 162 |

Cả ba phép so sánh đều trả về `True` cho điều kiện nội dung và thứ tự dòng giống nhau.

Kết quả xác nhận ba tệp Train/Dev/Test hiện đang được lưu trong `model_data` khớp chính xác với các phần tương ứng trong snapshot.

## 5. Đánh giá

Các kiểm tra hỗ trợ những kết luận sau:

1. Môi trường Python và các phiên bản thư viện chính đã được ghi nhận; danh sách phụ thuộc được lưu trong `requirements.txt`.
2. Tệp nguồn có gán split và snapshot có cùng SHA-256.
3. Ba tệp Train/Dev/Test khớp snapshot về danh sách cột, nội dung và thứ tự bản ghi.
4. Số mẫu, số documents và số nhãn Critical của từng tập khớp với manifest.
5. Manifest ghi nhận không có document overlap giữa Train, Dev và Test.

Do đó, các kiểm tra về môi trường và tính toàn vẹn của phép chia dữ liệu trong phạm vi G3.4 được xem là **đạt**.

## 6. Giới hạn và việc chưa được khẳng định

Kết quả trên xác nhận tính nhất quán của các tệp hiện có tại thời điểm kiểm tra. Chúng **không tự động chứng minh** rằng toàn bộ pipeline có thể được tái tạo từ đầu trên một máy mới hoặc một bản checkout sạch.

Ngoài ra:

- `verify_locked_split.py` hiện chủ yếu in kết quả; chưa bảo đảm mọi sai lệch đều khiến chương trình kết thúc với trạng thái lỗi.
- Việc đối chiếu ba tệp Train/Dev/Test với snapshot đã được thực hiện bằng một đoạn kiểm tra độc lập trong phiên làm việc này; chưa có bằng chứng phép đối chiếu đó đã được tích hợp vào `verify_locked_split.py`.
- Manifest có trạng thái `candidate_locked`; báo cáo này không diễn giải trạng thái đó thành cơ chế khóa bất biến ở cấp hệ thống.
- Tái chạy toàn bộ workflow từ đầu và xác nhận đầu ra được tạo lại nhất quán thuộc phạm vi kiểm chứng workflow tiếp theo của G3, không được coi là đã hoàn tất chỉ dựa trên các phép kiểm tra trong báo cáo này.

## 7. Kết luận G3.4

**G3.4 – Kiểm chứng môi trường và tính toàn vẹn của phép chia dữ liệu: ĐẠT trong phạm vi các kiểm tra đã thực hiện.**

Bằng chứng hiện có đủ để xác nhận môi trường thực thi chính, hash của snapshot, và sự tương ứng chính xác giữa snapshot với các tệp Train/Dev/Test đang được sử dụng.

G3.4 không đồng nghĩa với việc toàn bộ G3 đã hoàn thành. Các bước tiếp theo vẫn cần kiểm tra verifier theo hướng fail-fast, xác nhận workflow tái lập trong điều kiện kiểm soát, và tổng hợp báo cáo reproducibility cuối cùng.
