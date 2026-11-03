# G1.4 – Feature Provenance Audit

**Trạng thái:** Đã kiểm tra mã nguồn chính được cung cấp.  
**Phạm vi mã nguồn:** `src/run_baselines.py`, `src/run_ablation_dev.py`, `src/evaluate_test_week10.py`, `experiments/sensitivity_analysis_week10.py`, `src/build_model_dataset.py`.

## 1. Mục tiêu

Xác định chính xác thông tin nào được đưa vào feature matrix của mô hình, nguồn gốc của từng nhóm đặc trưng, và liệu các biến được tạo từ annotation MQM có bị sử dụng làm đầu vào dự đoán hay không.

## 2. Feature provenance của baseline chính

Trong `src/run_baselines.py`, feature matrix được tạo từ hai nhóm:

### A. TF-IDF source và target

- TF-IDF riêng cho `source`.
- TF-IDF riêng cho `target`.
- `ngram_range=(1, 2)`.
- `max_features=30000`.
- `min_df=2`.
- `sublinear_tf=True`.

Hai vectorizer được fit bằng `train_df["source"]` và `train_df["target"]`; Dev chỉ được transform bằng vectorizer đã fit.

### B. 12 surface features

| # | Đặc trưng | Nguồn |
|---:|---|---|
| 1 | `log1p(source token count)` | Source |
| 2 | `log1p(target token count)` | Target |
| 3 | Target/source token ratio | Source + target |
| 4 | Absolute token-length difference / source length | Source + target |
| 5 | Character-length ratio | Source + target |
| 6 | Number of digits in source | Source |
| 7 | Number of digits in target | Target |
| 8 | Absolute digit-count difference | Source + target |
| 9 | Uppercase-character ratio in target | Target |
| 10 | Punctuation/symbol-character ratio in target | Target |
| 11 | Repeated-token count in target | Target |
| 12 | Empty-target indicator | Target |

Không có đặc trưng nào trong danh sách trên trực tiếp đọc `category`, `severity`, `rater`, `serious_votes` hoặc `y_primary`.

## 3. Feature provenance trong ablation

`src/run_ablation_dev.py` tạo ba cấu hình:

1. `LR_Base`: TF-IDF source/target + 12 surface features.
2. `LR_Plus_System`: Base features + one-hot `system`.
3. `System_Only`: chỉ one-hot `system`.

One-hot encoder được fit trên Train và transform Dev. Do đó `system` chỉ được dùng trong hai cấu hình ablation có chủ đích, không phải feature của baseline `LR_Base` hoặc `LinearSVM` trong `run_baselines.py`.

`system` là metadata có thể biết khi triển khai trên các hệ thống MT đã xác định. Tuy nhiên, kết quả của cấu hình có system identity không tự động chứng minh khả năng tổng quát hóa sang một hệ thống MT hoàn toàn mới.

## 4. Các trường được giữ trong bảng nhưng không phải feature

`build_model_dataset.py` tạo và lưu các cột `distinct_raters`, `serious_votes`, `y_primary` để phục vụ kiểm toán nhãn và đánh giá. Trong các mã nguồn huấn luyện được kiểm tra, feature matrix được xây dựng tường minh từ `source`, `target` và 12 surface features; không đưa những cột nhãn/annotation này vào `hstack`.

Trong `run_baselines.py`, `serious_votes` và `y_primary` được đưa vào `dev_predictions` ở bước lưu kết quả và phân tích tương quan sau khi mô hình đã tạo score. Chúng không được truyền vào `model.fit()` hoặc `model.predict`/`decision_function`.

Trong `evaluate_test_week10.py`, `y_primary` được dùng làm target `y_fit` và `y_test`, không phải feature. Các cột định danh và văn bản được lưu cùng prediction để truy vết và error analysis, không được ghép vào feature matrix.

## 5. Kết luận

Theo các mã nguồn đã kiểm tra, feature provenance của baseline chính là reference-free: mô hình sử dụng source, bản dịch MT gốc và các đặc trưng bề mặt được tính từ hai chuỗi này. Không thấy bằng chứng các trường annotation MQM hoặc nhãn mục tiêu bị đưa trực tiếp vào feature matrix. System identity chỉ xuất hiện trong các cấu hình ablation được đặt tên rõ ràng.

Kết luận này áp dụng cho đúng các file mã nguồn được kiểm tra; không khẳng định mọi script hoặc checkpoint ngoài phạm vi cung cấp đều có cùng hành vi.
