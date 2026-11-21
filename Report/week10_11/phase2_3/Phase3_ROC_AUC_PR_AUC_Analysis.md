# Phase 3 – Bổ sung ROC-AUC và phân tích PR-AUC

## 1. Mục tiêu

Giai đoạn này bổ sung ROC-AUC vào kết quả đánh giá hiện có, đồng thời làm rõ sự khác biệt giữa ROC-AUC và PR-AUC trong bài toán Reference-Free Critical Error Detection.

Việc tính toán được thực hiện trên các điểm dự đoán đã lưu tại:

`results/week10/test_evaluation/test_predictions.csv`

Không huấn luyện lại mô hình và không tạo dự đoán mới. Các chỉ số được tính trực tiếp từ cột nhãn `y_primary` và các cột điểm dự đoán có sẵn.

## 2. Kiểm tra dữ liệu đầu vào

| Thuộc tính | Kết quả |
|---|---:|
| Số mẫu | 1.575 |
| Số cột | 11 |
| Số mẫu dương tính (`y_primary = 1`) | 162 |
| Số mẫu âm tính (`y_primary = 0`) | 1.413 |
| Tỷ lệ dương tính (prevalence) | 10,2857% |
| Giá trị thiếu | 0 |

Các cột điểm dự đoán được sử dụng:

- `score_Random`
- `score_HeuristicRules`
- `score_LogisticRegression`
- `score_LinearSVM`

Cột nhãn chuẩn là `y_primary`.

## 3. Kết quả ROC-AUC và PR-AUC

PR-AUC trong báo cáo này được tính bằng `average_precision_score` của scikit-learn. Vì vậy, tên gọi chính xác nên là **Average Precision (AP)** hoặc **PR-AUC (AP)**. Không nên mô tả kết quả này như diện tích hình học được tính bằng quy tắc hình thang nếu chưa thực hiện phép tính đó.

| Phương pháp | ROC-AUC | PR-AUC (Average Precision) |
|---|---:|---:|
| Random | 0.499703 | 0.109065 |
| Heuristic | 0.558229 | 0.139147 |
| Logistic Regression | **0.629942** | **0.197118** |
| Linear SVM | 0.614455 | 0.167623 |

Các giá trị trên được tính lại từ file dự đoán đã lưu. Kết quả xác nhận các con số sơ bộ trước đó.

## 4. Giải thích ROC-AUC và PR-AUC

### 4.1. ROC-AUC

ROC-AUC đo khả năng xếp hạng mẫu dương tính cao hơn mẫu âm tính trên toàn bộ các ngưỡng phân loại. ROC curve biểu diễn quan hệ giữa:

- True Positive Rate (TPR, Recall): tỷ lệ mẫu dương tính được phát hiện.
- False Positive Rate (FPR): tỷ lệ mẫu âm tính bị phân loại nhầm thành dương tính.

ROC-AUC càng cao thì khả năng phân biệt hai lớp càng tốt. Giá trị xấp xỉ 0.5 tương ứng với mức phân biệt gần ngẫu nhiên.

Trong kết quả này, Logistic Regression đạt ROC-AUC 0.629942, cao nhất trong bốn phương pháp. Linear SVM đạt 0.614455, Heuristic đạt 0.558229 và Random đạt 0.499703.

### 4.2. PR-AUC / Average Precision

Precision–Recall curve biểu diễn quan hệ giữa Precision và Recall khi thay đổi ngưỡng phân loại. Average Precision tổng hợp độ chính xác tại các mức Recall khác nhau, có xét đến mức tăng Recall giữa các điểm liên tiếp.

Trong bài toán này, lớp dương tính chỉ chiếm 10.2857% dữ liệu Test. Vì vậy, PR-AUC/AP đặc biệt hữu ích để đánh giá chất lượng xếp hạng đối với lớp lỗi nghiêm trọng, thay vì chỉ xem xét khả năng phân biệt tổng thể.

Mức AP nền của một bộ xếp hạng ngẫu nhiên thường xấp xỉ tỷ lệ dương tính của tập dữ liệu, ở đây là 0.102857. Random đạt AP 0.109065, gần mức nền này. Logistic Regression đạt 0.197118, cao hơn mức nền, nhưng vẫn còn cách xa mức hiệu quả hoàn hảo.

### 4.3. Vì sao cần báo cáo cả hai?

ROC-AUC đánh giá khả năng phân biệt trên toàn bộ các ngưỡng và cả hai lớp. Trong dữ liệu mất cân bằng, số lượng mẫu âm tính lớn có thể khiến ROC-AUC chưa phản ánh rõ mức độ chính xác khi ưu tiên dự đoán lớp dương tính.

PR-AUC/AP tập trung vào sự đánh đổi giữa Precision và Recall của lớp dương tính, do đó cung cấp góc nhìn phù hợp hơn khi mục tiêu là tìm các lỗi nghiêm trọng vốn tương đối hiếm.

Hai chỉ số bổ sung cho nhau, không thay thế nhau. Đối với hệ thống Second Pair of Eyes, cả hai cần được đọc cùng Recall@20%, Precision@20% và Lift@20%, bởi hệ thống hướng đến ưu tiên một phần bản dịch trong điều kiện ngân sách rà soát cố định.

## 5. Nhận xét kết quả

### 5.1. Logistic Regression

Logistic Regression đạt ROC-AUC 0.629942 và AP 0.197118, cao nhất trong các phương pháp được so sánh. Kết quả cho thấy mô hình có khả năng xếp hạng mẫu lỗi nghiêm trọng tốt hơn Heuristic, Linear SVM và Random trên tập Test này.

Tuy nhiên, ROC-AUC vẫn ở mức khiêm tốn. AP 0.197118 cũng cần được đặt trong bối cảnh tỷ lệ dương tính chỉ là 10.2857%. Vì vậy, kết quả cho thấy có tín hiệu dự đoán hữu ích, nhưng chưa đủ để khẳng định mô hình có năng lực phát hiện lỗi mạnh hoặc đã sẵn sàng triển khai.

### 5.2. Linear SVM

Linear SVM đạt ROC-AUC 0.614455 và AP 0.167623. Cả hai chỉ số đều thấp hơn Logistic Regression trong lần đánh giá này.

Điểm dự đoán của Linear SVM có thể âm. Điều đó không phải lỗi dữ liệu: ROC-AUC và Average Precision sử dụng thứ tự tương đối của điểm dự đoán, không yêu cầu điểm phải nằm trong khoảng [0, 1].

### 5.3. Heuristic và Random

Heuristic đạt ROC-AUC 0.558229 và AP 0.139147, cao hơn Random nhưng thấp hơn hai mô hình học máy. Random đạt ROC-AUC 0.499703 và AP 0.109065, gần các mức nền tương ứng.

Kết quả này cho thấy Heuristic có tín hiệu xếp hạng nhất định, nhưng hiệu quả vẫn hạn chế.

## 6. Liên hệ với ngân sách rà soát 20%

ROC-AUC và AP đánh giá thứ hạng trên nhiều ngưỡng. Trong khi đó, hệ thống được định hướng vận hành như một hàng đợi ưu tiên với ngân sách rà soát cố định 20%.

Với 1.575 mẫu Test, 20% tương ứng 315 mẫu được ưu tiên rà soát. Các kết quả Recall@20% đã ghi nhận trước đó:

| Phương pháp | Số lỗi nghiêm trọng tìm thấy trong top 20% | Recall@20% |
|---|---:|---:|
| Logistic Regression | 51/162 | 0.3148 |
| Heuristic | 50/162 | 0.3086 |

Logistic Regression chỉ tìm thêm một mẫu dương tính so với Heuristic trong top 20%. Do đó, dù Logistic Regression có ROC-AUC và AP cao hơn, mức cải thiện vận hành tại ngân sách 20% là nhỏ. Không nên tuyên bố mô hình vượt trội rõ rệt về hiệu quả ưu tiên rà soát chỉ dựa trên kết quả này.

## 7. Kết luận Phase 3

1. Đã bổ sung và xác nhận ROC-AUC cho cả bốn phương pháp từ file dự đoán đã lưu.
2. Logistic Regression đạt kết quả cao nhất với ROC-AUC = 0.629942 và AP = 0.197118.
3. AP cần được ghi rõ là Average Precision, không đánh đồng với diện tích PR curve tính bằng quy tắc hình thang.
4. Do tỷ lệ dương tính chỉ là 10.2857%, PR-AUC/AP là chỉ số quan trọng để đánh giá khả năng xếp hạng lớp lỗi nghiêm trọng.
5. ROC-AUC và AP không thay thế các chỉ số gắn với ngân sách rà soát. Recall@20% cho thấy Logistic Regression chỉ phát hiện thêm một lỗi nghiêm trọng so với Heuristic trong top 20%.
6. Kết quả hiện tại chưa đủ để kết luận mô hình có hiệu quả vận hành vượt trội. Cần tiếp tục phân tích False Negative và False Positive để xác định mô hình bỏ sót loại lỗi nào và vì sao.

## 8. Phạm vi và giới hạn

- Phân tích này sử dụng file dự đoán Test đã tồn tại; không huấn luyện lại mô hình.
- Các chỉ số phản ánh kết quả trên split Test hiện có, không tự chứng minh rằng Test chưa từng được quan sát hoặc sử dụng trong quá trình phát triển. Giới hạn về bằng chứng lịch sử sử dụng Test được trình bày riêng trong báo cáo Phase 2.
- Chưa thực hiện đánh giá cuối cùng độc lập.
- Chưa sử dụng kết quả Phase 3 để điều chỉnh ngưỡng, lựa chọn mô hình mới hoặc huấn luyện lại.

## 9. Bước tiếp theo

Chuyển sang Phase 4: phân tích False Negative và False Positive, ưu tiên xác định các nhóm lỗi MQM bị bỏ sót, mức độ nghiêm trọng, đặc điểm bản dịch và các trường hợp mà nhãn đa số của người gán nhãn có thể chưa phản ánh đầy đủ lỗi thực tế.
