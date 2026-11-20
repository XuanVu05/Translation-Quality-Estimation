# Phase 2 – Kiểm toán lịch sử Git và tính toàn vẹn của tập Test

## 1. Mục tiêu

Kiểm tra lịch sử Git, split manifest, snapshot dữ liệu, mã đánh giá và thời điểm các tệp kết quả được ghi nhận nhằm xác định mức độ có thể chứng minh về tính độc lập của tập Test.

Phạm vi kiểm toán này chỉ sử dụng bằng chứng hiện có trong repository và các đầu ra PowerShell do người thực hiện cung cấp. Không chạy lại mô hình, không tạo dự đoán mới và không sử dụng Test cho bất kỳ quyết định mô hình nào.

## 2. Bằng chứng về split và dữ liệu

Manifest tại `results/week10/locked_split/manifest.json` ghi nhận:

- Trạng thái: `candidate_locked`.
- Thời điểm tạo được ghi trong manifest: `2026-10-28T10:42:19.951380+00:00`.
- Phương pháp: `GroupShuffleSplit` theo `doc`.
- Random state: 42 và 43.
- Tỷ lệ mục tiêu: Train 70%, Dev 15%, Test 15%.
- Tổng số: 9.926 dòng, 130 tài liệu, 1.183 mẫu dương.
- Train: 6.797 dòng, 90 tài liệu, 803 mẫu dương.
- Dev: 1.554 dòng, 20 tài liệu, 218 mẫu dương.
- Test: 1.575 dòng, 20 tài liệu, 162 mẫu dương.
- Số tài liệu giao nhau giữa các cặp split đều bằng 0.

SHA-256 của tệp nguồn `segments_with_fixed_splits.csv` và snapshot `segments_week10_90_20_20.csv` trùng nhau:
`780cd9f0b2b32042ad95f98e67318c03814fbe895e1f0ef8755da847e8d287ab`.

QA report xác nhận không có missing values, không có duplicate theo khóa `system/doc/seg_id`, không có document overlap và hash nguồn/snapshot trùng nhau. Tuy nhiên, chính QA report nêu rõ script kiểm tra và snapshot split hiện có, không tự tái tạo độc lập split từ dữ liệu raw.

Git diff giữa `fbea822` và `142fa90` cho thấy snapshot split được thêm vào ở commit `142fa90` (9.927 dòng bao gồm header), trong khi `segments_with_fixed_splits.csv` không thay đổi so với commit đầu tiên. Lịch sử file cho thấy dữ liệu `segments_with_fixed_splits.csv` đã có trong commit đầu tiên `fbea822`.

## 3. Bằng chứng về mã nguồn đánh giá Test

Lịch sử `src/evaluate_test_week10.py`:

- `fbea822` – 27/10/2026 22:18:38 +0700: Initial commit.
- `a810ff1` – 28/10/2026 16:47:59 +0700: Refactor codebase.

Diff giữa hai commit chỉ thay đổi cách xác định thư mục gốc:

```python
# Trước
ROOT = Path(r"D:\Translation Quality Estimation")

# Sau
ROOT = Path(__file__).resolve().parent.parent
```

Không có thay đổi logic đánh giá được thể hiện trong diff này.

Nội dung script tại commit đầu tiên cho thấy:

1. Ghép Train và Dev thành `fit_df`.
2. Fit TF-IDF vectorizers trên văn bản của `fit_df`.
3. Fit `StandardScaler` trên surface features của `fit_df`.
4. Dùng `transform()` cho dữ liệu Test.
5. Huấn luyện Logistic Regression và Linear SVM trên `X_fit, y_fit`.
6. Sinh score cho Test, lưu `test_predictions.csv` và tính các metric dựa trên `y_test`.

Vì vậy, xét riêng mã nguồn được lưu trong Git, quy trình fit preprocessing và mô hình không fit trực tiếp trên Test. Đây là bằng chứng về thiết kế mã nguồn, không phải bằng chứng đầy đủ về hành vi thực thi hoặc việc sử dụng kết quả Test trong quá trình ra quyết định.

README hiện tại quy định preprocessing cho Dev được fit trên Train và pipeline đánh giá Test được refit trên Train + Dev. Tuy nhiên, phần README ở commit đầu tiên được kiểm tra không cho thấy các quy định này. Không dùng README hiện tại để suy ngược rằng quy trình đã được ghi thành quy định ngay từ commit đầu tiên.

## 4. Trình tự xuất hiện của các kết quả trong Git

Các lịch sử file được kiểm tra cho thấy:

| Tệp | Commit đầu tiên được ghi nhận | Thời điểm |
|---|---|---|
| `results/week10/test_evaluation/test_point_metrics.csv` | `fbea822` | 27/10/2026 22:18:38 +0700 |
| `results/week10/test_evaluation/test_predictions.csv` | `fbea822` | 27/10/2026 22:18:38 +0700 |
| `results/week10/ablation_dev/dev_ablation_metrics.csv` | `142fa90` | 29/10/2026 00:00:12 +0700 |
| `results/week10/ablation_dev/dev_ablation_predictions.csv` | `142fa90` | 29/10/2026 00:00:12 +0700 |
| `results/week10/locked_split/manifest.json` | `142fa90` | 29/10/2026 00:00:12 +0700 |

Manifest ghi `created_at_utc` là 28/10/2026 10:42:19 UTC (tương đương 17:42:19 +0700), trước commit `142fa90` nhưng sau commit đầu tiên `fbea822`.

Điểm quan trọng: hai tệp Test predictions và Test point metrics đã được commit trong `fbea822`, trước khi các tệp Dev ablation và manifest xuất hiện trong lịch sử Git. Vì thế, lịch sử Git hiện tại không chứng minh được rằng Test chỉ được đánh giá sau khi split được khóa và sau khi lựa chọn mô hình hoàn tất.

Thứ tự commit chỉ chứng minh thời điểm các tệp được ghi nhận trong Git. Nó không xác định chính xác thời điểm tệp được tạo hoặc chạy, vì các tệp có thể đã tồn tại cục bộ trước khi commit. Cũng không thể loại trừ khả năng kết quả Dev đã được tạo trước nhưng chỉ được commit sau.

Lệnh tìm `reports/G2_model_evaluation.md` không trả về kết quả. Điều này chỉ cho thấy không có lịch sử file tại đúng đường dẫn đó; chưa đủ cơ sở để kết luận repository không có tài liệu G2 với tên hoặc đường dẫn khác.

## 5. Kết luận theo mức độ bằng chứng

### Đã xác minh

- Script đánh giá Test tại commit đầu tiên fit TF-IDF, scaler, Logistic Regression và Linear SVM trên Train + Dev.
- Script dùng các thành phần đã fit để transform Test.
- Tệp Test predictions và Test point metrics đã được ghi nhận trong commit đầu tiên ngày 27/10/2026.
- Dữ liệu split hiện có có 130 tài liệu, không có document overlap giữa Train, Dev và Test.
- SHA-256 của source CSV và snapshot CSV trùng nhau.
- `segments_with_fixed_splits.csv` đã tồn tại từ commit đầu tiên và không thay đổi giữa `fbea822` và `142fa90`.
- Các tệp Dev ablation và manifest được ghi nhận trong commit ngày 29/10/2026, sau commit đầu tiên chứa kết quả Test.

### Chưa đủ bằng chứng

- Không thể chứng minh Test chưa từng được xem, kiểm tra hoặc dùng để lựa chọn mô hình.
- Không thể chứng minh split đã được khóa trước lần đánh giá Test đầu tiên.
- Không thể xác định chỉ từ Git liệu kết quả Dev đã tồn tại cục bộ trước khi các tệp Test được commit hay chưa.
- Không thể xác định ai đã chạy script, thời điểm chạy thực tế, hoặc các quyết định mô hình có bị ảnh hưởng bởi kết quả Test hay không.

## 6. Cách diễn đạt phù hợp trong báo cáo học thuật

Có thể sử dụng cách diễn đạt sau:

> Mã nguồn đánh giá được lưu trong repository cho thấy các bộ biến đổi đặc trưng và mô hình được fit trên tập Train kết hợp Dev, trong khi Test chỉ được sử dụng ở bước biến đổi, dự đoán và tính toán metric. Việc kiểm tra split manifest và snapshot xác nhận không có giao nhau về tài liệu giữa ba tập dữ liệu và hash của tệp nguồn với snapshot là trùng khớp. Tuy nhiên, lịch sử Git cho thấy các tệp Test predictions và Test point metrics đã được ghi nhận trong commit đầu tiên ngày 27/10/2026, trong khi các kết quả Dev ablation và manifest được ghi nhận ở commit ngày 29/10/2026. Do Git chỉ phản ánh thời điểm commit chứ không nhất thiết là thời điểm tạo tệp hoặc thực hiện thí nghiệm, bằng chứng hiện có chưa đủ để khẳng định Test hoàn toàn không được xem hoặc không ảnh hưởng đến quá trình lựa chọn mô hình. Vì vậy, nghiên cứu xác nhận được tính đúng đắn của thiết kế fit/transform trong mã nguồn và tính nhất quán của split hiện tại, nhưng không đưa ra tuyên bố tuyệt đối về tính độc lập lịch sử của Test.

## 7. Quyết định vận hành

- Tiếp tục giữ Test ở trạng thái không sử dụng cho phát triển mô hình.
- Không chạy lại `evaluate_test_week10.py` trong giai đoạn phân tích và phát triển tiếp theo.
- Không dùng kết quả Test để chọn feature, mô hình, threshold hoặc hyperparameter.
- Các thử nghiệm tiếp theo, nếu được phê duyệt, chỉ sử dụng Train và Dev.
- Chỉ cân nhắc một đánh giá cuối cùng độc lập sau khi hoàn tất các phân tích và quyết định mô hình trên Dev; cần ghi rõ giới hạn lịch sử nêu trong báo cáo này.

## 8. Phạm vi và giới hạn

Báo cáo này là kiểm toán bằng chứng repository, không phải kiểm toán hệ thống thực thi. Git không lưu nhật ký đầy đủ về lệnh đã chạy, thời điểm chạy, người xem kết quả, hoặc quá trình ra quyết định. Do đó, kết luận được giới hạn ở những gì có thể xác minh từ lịch sử commit, nội dung mã nguồn, manifest, QA report và các đầu ra đã cung cấp.
