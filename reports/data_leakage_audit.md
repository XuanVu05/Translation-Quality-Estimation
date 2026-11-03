# G1.4 – Data Leakage Audit

**Trạng thái:** Đã kiểm tra mã nguồn huấn luyện, đánh giá và chia tập được cung cấp.  
**Kết luận tổng quát:** Không phát hiện label leakage trực tiếp trong feature matrix của các pipeline được kiểm tra. Quy trình preprocessing và chia tập theo document được triển khai đúng nguyên tắc. Có một số giới hạn về kiểm chứng tự động và tính nhất quán của baseline cần ghi rõ.

## 1. Label leakage

### Kết quả: Không phát hiện trong pipeline LR/SVM được kiểm tra

- `y_primary` được dùng làm target khi gọi `model.fit`.
- `serious_votes` và `distinct_raters` không được ghép vào feature matrix.
- `category`, `severity`, `rater` không được sử dụng trong `text_features`, `surface_features` hoặc TF-IDF.
- `run_baselines.py` lưu `serious_votes` và `y_primary` trong bảng prediction để phân tích hậu nghiệm; thao tác này xảy ra sau khi scores đã được tạo và không ảnh hưởng đến model fitting.

## 2. Preprocessing leakage

### Development baseline – `src/run_baselines.py`

- TF-IDF source và target: `fit_transform` trên Train; `transform` trên Dev.
- `StandardScaler`: `fit_transform` trên surface features Train; `transform` trên Dev.
- Test không được nạp trong script phát triển mô hình.

### Ablation – `src/run_ablation_dev.py`

- TF-IDF và scaler chỉ fit trên Train.
- OneHotEncoder cho `system` chỉ fit trên Train; Dev được transform.
- Manifest ghi `test_set_loaded: false`.

### Label sensitivity – `experiments/sensitivity_analysis_week10.py`

- Vectorizer và scaler chỉ fit trên Train.
- Chỉ nạp Train và Dev; Test không được đọc.

### Final Test evaluation – `src/evaluate_test_week10.py`

- Mô hình cuối được fit trên `Train + Dev`, sau khi lựa chọn mô hình đã được cố định từ kết quả phát triển.
- TF-IDF và scaler được fit trên `Train + Dev`; Test chỉ được transform.
- Đây là quy trình hợp lệ cho đánh giá cuối cùng khi Test chưa được dùng để lựa chọn mô hình hoặc siêu tham số.

## 3. Document leakage

`src/split_by_document.py` sử dụng `GroupShuffleSplit` với `groups=df["doc"]`. Sau khi chia, script kiểm tra giao giữa document của Train/Dev/Test và raise lỗi nếu phát hiện overlap.

Các kết quả dự án đã ghi nhận trước đó là 90 documents Train, 20 Dev và 20 Test; không có document overlap. Split hash được ghi nhận trong nhật ký dự án: `780cd9f0b2b32042ad95f8e67318c03814fbe895e1f0ef8755da847e8d287ab`.

**Phạm vi cần phân biệt:** Mã `split_by_document.py` được cung cấp mô tả cách tạo split ngẫu nhiên theo document. Mã `verify_locked_split.py` kiểm tra snapshot, hash, assignments và document-to-split consistency bằng cách in kết quả. Việc xác nhận thực tế các file snapshot trong máy người dùng cần dựa trên stdout của lần chạy script đó.

## 4. Test-set isolation và model selection

Trong `run_baselines.py`, chỉ Train và Dev được nạp; chú thích trong mã nêu rõ Test không được nạp trong giai đoạn phát triển. LR và SVM được đánh giá trên Dev.

Trong `run_ablation_dev.py`, chỉ Train và Dev được nạp; manifest đánh dấu `test_set_loaded: false`.

Trong `evaluate_test_week10.py`, mô hình được fit trên Train + Dev và đánh giá trên Test. Chú thích trong mã nêu model choice đã được cố định từ development results. Mã không thực hiện tìm kiếm siêu tham số trên Test; các cấu hình LR/SVM trong script có `C=1.0`.

## 5. Các điểm cần lưu ý – không đồng nghĩa với leakage

1. **System identity:** Ablation có cấu hình sử dụng one-hot system. Đây là feature metadata có chủ đích, không phải nhãn MQM. Tuy nhiên, cần giới hạn kết luận về khả năng tổng quát hóa sang hệ thống MT mới.
2. **Random baseline:** Development baseline lấy trung bình 100 random rankings; test evaluation dùng một random ranking với seed cố định. Đây không phải leakage, nhưng độ ổn định của random baseline trên Test chưa được phản ánh bằng nhiều lần chạy.
3. **Split verifier:** `verify_locked_split.py` in ra kết quả kiểm tra nhưng không raise lỗi khi hash hoặc assignments không khớp. Vì vậy, nó là script báo cáo kiểm tra, chưa phải automated gate nghiêm ngặt.
4. **Split provenance:** `split_by_document.py` kiểm tra không trùng document. Việc xác nhận snapshot đã khóa và đúng hash cần lưu stdout của `verify_locked_split.py` cùng snapshot và assignment files.
5. **Parser consistency:** Các script đọc TSV MQM không hoàn toàn dùng cùng cấu hình parser. Do dự án từng ghi nhận sai khác khi đọc TSV, nên nên thống nhất parser trong các script tái dựng nhãn và error analysis. Đây là rủi ro reproducibility/data consistency, không phải bằng chứng label leakage trong LR/SVM.

## 6. Kết luận kiểm toán

Trong các file được cung cấp, không phát hiện bằng chứng trực tiếp của label leakage hoặc preprocessing leakage trong baseline LR/SVM, ablation Dev và final Test evaluation. Vectorizers/scaler được fit trên phần dữ liệu huấn luyện tương ứng; Test được giữ ngoài giai đoạn phát triển và chỉ transform ở final evaluation. Chia tập theo document được triển khai bằng `GroupShuffleSplit` và có kiểm tra overlap.

Do đó, G1.4 có thể được xem là **đạt có điều kiện**. Điều kiện là lưu bằng chứng chạy kiểm tra split đã khóa, thống nhất parser MQM, và mô tả rõ system identity là một cấu hình ablation chứ không phải feature của baseline chính.
