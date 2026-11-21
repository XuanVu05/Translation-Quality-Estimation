# G3.5.2 -- Tái lập các mô hình Baseline trên tập Dev

## 1. Mục tiêu

Giai đoạn G3.5.2 nhằm xác minh khả năng tái lập các kết quả Baseline của
Week 10 trên tập phát triển (Dev) trong một thư mục sandbox độc lập. Quá
trình sử dụng cùng trình thông dịch Python, mã nguồn, dữ liệu đầu vào và
phép chia Train/Dev đã được kiểm chứng ở các giai đoạn trước.

Thư mục thực nghiệm:

`D:\MLA_Reproduction_Test`

Trình thông dịch Python:

`D:\Translation-Quality-Estimation\.venv_mla\python.exe`

## 2. Quy trình thực hiện

Chạy lệnh sau tại thư mục sandbox:

``` powershell
& "D:\Translation-Quality-Estimation\.venv_mla\python.exe" .\src\run_baselines.py
```

Script sử dụng Train và Dev để xây dựng và đánh giá các mô hình
Baseline. Tập Test không được nạp hoặc sử dụng trong giai đoạn này.

Các tệp đầu ra:

-   `results/week10/baseline_results/dev_baseline_metrics.csv`
-   `results/week10/baseline_results/dev_baseline_metrics.json`
-   `results/week10/priority2_3/dev_model_predictions_with_votes.csv`
-   `results/week10/priority2_3/dev_model_ranking_by_serious_votes.csv`
-   `results/week10/priority2_3/dev_model_vote_correlations.csv`

## 3. Kết quả Baseline trên tập Dev

Tập Dev gồm 1.554 mẫu, trong đó có 218 mẫu Critical. Ngân sách rà soát
top-20% tương ứng 311 mẫu.

  ----------------------------------------------------------------------------------------
  Mô hình                    PR-AUC   Recall@20%   Precision@20%     Lift@20%      MCC@20%
  -------------------- ------------ ------------ --------------- ------------ ------------
  Random                   0.143502     0.199633        0.139936     0.997523    -0.000500

  HeuristicRules           0.177704     0.330275        0.231511     1.650314     0.131399

  LogisticRegression       0.196052     0.288991        0.202572     1.444025     0.089717

  LinearSVM                0.174222     0.275229        0.192926     1.375262     0.075824
  ----------------------------------------------------------------------------------------

## 4. Đối chiếu trực tiếp với kết quả gốc

Tệp metric trong dự án gốc và tệp metric được tạo trong sandbox được đối
chiếu trực tiếp theo hai trường `model` và `metric`.

Kết quả kiểm tra:

-   Tất cả 27 dòng model--metric đều xuất hiện trong cả hai tệp.
-   Toàn bộ giá trị trung bình (`mean`) giống nhau.
-   Toàn bộ độ lệch chuẩn (`std`) giống nhau.
-   Chênh lệch giữa giá trị gốc và giá trị tái lập bằng 0.0 ở tất cả các
    dòng.

Các metric được kiểm tra bao gồm PR-AUC, Recall@20%, Precision@20%,
Lift@20%, MCC@20%, `n_top` và prevalence.

**Kết quả: PASS.** Các metric Baseline trên tập Dev được tái lập chính
xác trong phép đối chiếu trực tiếp.

## 5. Phân tích bổ sung theo số lượt serious votes

Script cũng tạo phân tích tương quan giữa điểm số mô hình và số lượt
serious votes:

  Mô hình                Spearman ρ
  -------------------- ------------
  LogisticRegression         0.0929
  LinearSVM                  0.1047

Cả hai hệ số tương quan đều dương nhưng yếu. Các p-value đi kèm chỉ mang
tính mô tả vì các quan sát có thể phụ thuộc lẫn nhau trong cùng document
và MT system. Do đó, không nên diễn giải chúng như bằng chứng suy luận
thống kê trên các quan sát độc lập.

Các tệp phân tích theo serious votes là kết quả bổ sung, không làm thay
đổi quy trình đánh giá Baseline.

## 6. Giới hạn về khả năng tái lập

Thực nghiệm xác nhận khả năng tái lập chính xác các metric Baseline trên
tập Dev trong cùng môi trường Python cục bộ đã được xác minh, với cùng
dữ liệu đầu vào và cùng phép chia dữ liệu.

Kết quả này chưa chứng minh khả năng tái lập trên máy tính độc lập hoặc
môi trường hoàn toàn mới. Thực nghiệm cũng không chứng minh khả năng
tổng quát hóa sang MT system chưa xuất hiện, cặp ngôn ngữ khác hoặc miền
dữ liệu khác.

Tập Test không được sử dụng trong giai đoạn này.

## 7. Vị trí lưu bằng chứng

Thư mục kết quả Baseline trong sandbox:

`D:\MLA_Reproduction_Test\results\week10\baseline_results\`

Thư mục phân tích bổ sung:

`D:\MLA_Reproduction_Test\results\week10\priority2_3\`

Tệp metric gốc:

`D:\Translation-Quality-Estimation\results\week10\baseline_results\dev_baseline_metrics.csv`

Tệp metric tái lập:

`D:\MLA_Reproduction_Test\results\week10\baseline_results\dev_baseline_metrics.csv`

**Kết luận:** G3.5.2 hoàn thành. Phép đối chiếu trực tiếp xác nhận 27/27
dòng metric khớp chính xác, với sai khác bằng 0.0 ở cả giá trị trung
bình và độ lệch chuẩn.
