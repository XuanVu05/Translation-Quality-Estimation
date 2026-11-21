# G3.5.4 -- Tái lập thực nghiệm đánh giá cuối cùng trên tập Test

## 1. Mục tiêu

Giai đoạn G3.5.4 kiểm tra khả năng tái lập thực nghiệm đánh giá cuối
cùng trên tập Test của Week 10. Việc đối chiếu sử dụng các tệp kết quả
trong sandbox và các tệp được cung cấp từ dự án gốc.

Thư mục sandbox:

`D:\MLA_Reproduction_Test`

Trình thông dịch Python:

`D:\Translation-Quality-Estimation\.venv_mla\python.exe`

Thực nghiệm sử dụng cấu hình đã thiết lập trong script
`evaluate_test_week10.py`: huấn luyện trên Train + Dev, đánh giá trên
Test, random seed 20261026, 1.000 bootstrap replicates và bootstrap seed
20261027. Đơn vị lấy mẫu bootstrap là document.

## 2. Quy trình thực hiện

Lệnh đã chạy:

``` powershell
& "D:\Translation-Quality-Estimation\.venv_mla\python.exe" .\src\evaluate_test_week10.py
```

Script hoàn thành và lưu bốn tệp:

-   `results/week10/test_evaluation/test_predictions.csv`
-   `results/week10/test_evaluation/test_point_metrics.csv`
-   `results/week10/test_evaluation/test_metrics_with_ci.csv`
-   `results/week10/test_evaluation/paired_difference_ci.csv`

Log xác nhận có 1.575 mẫu Test, 20 documents, 162 mẫu Critical, tỷ lệ
Critical 0.10286 và 1.000 bootstrap replicates.

## 3. Kết quả đánh giá trên Test

  Mô hình                  PR-AUC   Recall@20%   Precision@20%   Lift@20%   MCC@20%
  -------------------- ---------- ------------ --------------- ---------- ---------
  Random                 0.109065     0.197531        0.101587   0.987654   -0.0021
  HeuristicRules           0.1391       0.3086          0.1587     1.5432    0.0920
  LogisticRegression       0.1971       0.3148          0.1619     1.5741    0.0972
  LinearSVM                0.1676       0.2346          0.1206     1.1728    0.0293

Test gồm 1.575 mẫu, trong đó có 162 mẫu Critical. Ngân sách rà soát
top-20% tương ứng 315 mẫu. Logistic Regression có PR-AUC cao nhất và
chọn được 51 mẫu Critical trong top-20%, so với 50 mẫu của
HeuristicRules.

## 4. Khoảng tin cậy 95% bằng Cluster Bootstrap

Khoảng tin cậy được tính bằng 1.000 lần bootstrap theo document. Một số
kết quả:

  Mô hình              Chỉ số      Ước lượng                   CI 95%
  -------------------- --------- ----------- ------------------------
  Random               PR-AUC       0.109065   \[0.076859, 0.155041\]
  HeuristicRules       PR-AUC         0.1391       \[0.0749, 0.2125\]
  LogisticRegression   PR-AUC         0.1971       \[0.1220, 0.2833\]
  LinearSVM            PR-AUC         0.1676       \[0.1055, 0.2564\]
  LogisticRegression   MCC@20%        0.0972       \[0.0176, 0.1880\]

Các khoảng tin cậy riêng lẻ mô tả độ bất định của từng ước lượng. Khi so
sánh hai mô hình trên cùng tập Test, cần ưu tiên paired differences vì
chúng giữ cấu trúc so sánh ghép cặp trên các document.

## 5. So sánh ghép cặp với HeuristicRules

  ------------------------------------------------------------------------------
  So sánh              Chỉ số                    Chênh lệch               CI 95%
  -------------------- --------------- -------------------- --------------------
  LogisticRegression − PR-AUC                     +0.057971          \[0.015118,
  HeuristicRules                                                      0.123220\]

  LogisticRegression − Recall@20%                 +0.006173         \[-0.088002,
  HeuristicRules                                                      0.181829\]

  LogisticRegression − Precision@20%              +0.003175         \[-0.052483,
  HeuristicRules                                                      0.082039\]

  LogisticRegression − Lift@20%                     +0.0309  \[-0.4393, 0.9075\]
  HeuristicRules

  LogisticRegression − MCC@20%                      +0.0052  \[-0.0798, 0.1376\]
  HeuristicRules
  ------------------------------------------------------------------------------

Trong các so sánh Logistic Regression với HeuristicRules, chỉ khoảng tin
cậy của chênh lệch PR-AUC không chứa 0. Các khoảng tin cậy của
Recall@20%, Precision@20%, Lift@20% và MCC@20% đều chứa 0.

Do đó, kết quả cung cấp bằng chứng về cải thiện PR-AUC của Logistic
Regression so với HeuristicRules, nhưng chưa đủ bằng chứng để kết luận
Logistic Regression vượt trội về hiệu quả lựa chọn mẫu trong ngân sách
rà soát 20%.

## 6. Đối chiếu trực tiếp với các tệp gốc

Bốn cặp tệp được đối chiếu gồm `test_predictions.csv`,
`test_point_metrics.csv`, `test_metrics_with_ci.csv` và
`paired_difference_ci.csv`.

  -----------------------------------------------------------------------------------------------------------------------------------------
  Tệp                                  Kích thước        Số dòng × cột SHA-256
  -------------------------- -------------------- -------------------- --------------------------------------------------------------------
  test_predictions.csv              774.835 bytes           1.575 × 11 `4f80d60c2da0b28ed2033a0994f6927e42cdbbb51fc242768f9dd10c73cc6022`

  test_point_metrics.csv                966 bytes               20 × 3 `40fdba6329f9169ed9aa957e07360632ef9e6860d8ab40abe88ee2bb92e2cd75`

  test_metrics_with_ci.csv            1.770 bytes               20 × 5 `ef42f1835e8cf529762a4693782f04d4311f2e6c756e5d249d9555e3398371b9`

  paired_difference_ci.csv            1.637 bytes               15 × 5 `5df1bfde44c7bed49450a7582826dd2c1be05e8fab1b773e31c2635424f3b0b1`
  -----------------------------------------------------------------------------------------------------------------------------------------

Kết quả đối chiếu giữa bốn tệp sandbox đã tải lên trước đó và bốn tệp
được cung cấp để đối chiếu với dự án gốc:

-   Kích thước từng cặp tệp giống nhau.
-   Số dòng, số cột và tên cột giống nhau.
-   `DataFrame.equals()` trả về `True` cho cả bốn cặp.
-   SHA-256 giống nhau cho cả bốn cặp.

Như vậy, cả bốn tệp kết quả giống hệt nhau ở cấp byte. Đây là bằng chứng
xác nhận tái lập chính xác các dự đoán Test, point estimates, khoảng tin
cậy bootstrap và paired differences giữa hai bộ kết quả được đối chiếu.

## 7. Giới hạn diễn giải

Tập Test chỉ gồm 20 documents thuộc cùng bộ dữ liệu WMT 2020
English--German và bảy MT systems đã nghiên cứu. Vì vậy, kết quả không
chứng minh khả năng tổng quát hóa sang ngôn ngữ, miền dữ liệu hoặc hệ
thống dịch máy chưa xuất hiện.

Việc các tệp kết quả giống hệt nhau xác nhận khả năng tái lập trong môi
trường và cấu hình đã sử dụng; không đồng nghĩa với việc đã chứng minh
khả năng tái lập trên một máy tính độc lập hoặc môi trường hoàn toàn
mới.

## 8. Kết luận

**G3.5.4: PASS.** Bốn tệp kết quả Test được đối chiếu giống hệt nhau ở
cấp byte giữa sandbox và bộ tệp gốc được cung cấp. Quy trình đánh giá
cuối cùng, bao gồm dự đoán từng mẫu, point estimates, cluster-bootstrap
confidence intervals và paired differences, được tái lập chính xác trong
phạm vi môi trường và cấu hình đã kiểm tra.
