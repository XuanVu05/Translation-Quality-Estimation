# G3.5.3 -- Tái lập thực nghiệm Ablation trên tập Dev

## 1. Mục tiêu

Giai đoạn G3.5.3 nhằm kiểm tra khả năng tái lập kết quả thực nghiệm
Ablation của Week 10 trên tập phát triển (Dev), sử dụng môi trường
Python, mã nguồn, dữ liệu đầu vào và phép chia Train/Dev đã được xác
minh ở các giai đoạn trước.

Thực nghiệm được thực hiện trong thư mục sandbox:

`D:\MLA_Reproduction_Test`

Trình thông dịch Python được sử dụng:

`D:\Translation-Quality-Estimation\.venv_mla\python.exe`

Tập Test không được nạp hoặc đánh giá trong giai đoạn này.

## 2. Quy trình thực hiện và các tệp đầu ra

Chạy lệnh sau tại thư mục sandbox:

``` powershell
& "D:\Translation-Quality-Estimation\.venv_mla\python.exe" .\src\run_ablation_dev.py
```

Kết quả thực thi xác nhận:

-   Tập Train có 6.797 mẫu thuộc 90 documents.
-   Tập Dev có 1.554 mẫu thuộc 20 documents.
-   Train có 803 mẫu Critical.
-   Dev có 218 mẫu Critical.
-   Ngân sách rà soát top-20% trên Dev là 311 mẫu.

Script tạo ba tệp:

-   `results/week10/ablation_dev/dev_ablation_metrics.csv`
-   `results/week10/ablation_dev/dev_ablation_predictions.csv`
-   `results/week10/ablation_dev/dev_ablation_manifest.json`

Log thực thi xác nhận rõ: `Test set was not loaded or evaluated.`

## 3. Các cấu hình Ablation

  -----------------------------------------------------------------------
  Mô hình                             Cấu hình đặc trưng
  ----------------------------------- -----------------------------------
  LR_Base                             TF-IDF của source/target kết hợp 12
                                      đặc trưng bề mặt

  LR_Plus_System                      Các đặc trưng của LR_Base cộng thêm
                                      one-hot MT system

  System_Only                         Chỉ sử dụng one-hot MT system
  -----------------------------------------------------------------------

Số chiều đặc trưng được ghi nhận lần lượt là 58.150 đối với LR_Base,
58.157 đối với LR_Plus_System và 7 đối với System_Only.

## 4. Kết quả thực nghiệm trên tập Dev

  Chỉ số                              LR_Base   LR_Plus_System   System_Only
  -------------------------------- ---------- ---------------- -------------
  PR-AUC                             0.196052         0.199116      0.156802
  Recall@20%                         0.288991         0.279817      0.252294
  Precision@20%                      0.202572         0.196141      0.176849
  Lift@20%                           1.444025         1.398183      1.260657
  MCC@20%                            0.089717         0.080455      0.052667
  Số mẫu được chọn trong top-20%          311              311           311
  Số mẫu Critical trong top-20%            63               61            55
  Tỷ lệ Critical của tập Dev         0.140283         0.140283      0.140283

## 5. Đối chiếu với kết quả gốc

Hai tệp CSV kết quả Ablation được cung cấp để đối chiếu đều có 24 dòng
và 8 cột. Nội dung các dòng, tên mô hình, mô tả, chỉ số, giá trị, số
lượng mẫu Train/Dev và số chiều đặc trưng đều giống nhau.

SHA-256 của hai tệp:

`e22a76dbea1aa4d16ec298e8f6ee211d0045a1709c940fcc75d854e9da2349b8`

Hai tệp giống nhau ở cấp byte. Tuy nhiên, tên tệp tải lên `(1)` và `(2)`
không đủ để xác định chắc chắn tệp nào được lấy từ dự án gốc và tệp nào
từ sandbox. Vì vậy, bằng chứng hiện có xác nhận tính đồng nhất của hai
tệp được cung cấp; để bảo đảm truy xuất nguồn gốc chặt chẽ, cần lưu lại
đường dẫn cục bộ tương ứng của từng tệp.

Các giá trị trong kết quả thực nghiệm cũng khớp với các kết quả Ablation
G2 đã ghi nhận trước đó cho cả ba cấu hình và các chỉ số được báo cáo.

**Đánh giá: PASS đối với phép đối chiếu hai tệp metric được cung cấp.**
Hai tệp CSV giống hệt nhau ở cấp byte và các giá trị tái lập khớp với
kết quả G2 đã ghi nhận.

## 6. Phân tích kết quả

Trên tập Dev, việc bổ sung thông tin MT system làm PR-AUC tăng nhẹ từ
0.196052 lên 0.199116. Tuy nhiên, Recall@20%, Precision@20%, Lift@20% và
MCC@20% đều giảm so với LR_Base.

Mô hình System_Only có giá trị thấp hơn LR_Base ở cả năm chỉ số chính.
Điều này cho thấy danh tính MT system có chứa tín hiệu dự báo, nhưng
riêng thông tin này chưa thể thay thế biểu diễn source/target và các đặc
trưng bề mặt.

MT system identity là đặc trưng siêu dữ liệu gắn với bảy hệ thống dịch
máy xuất hiện trong tập dữ liệu. Kết quả Ablation này không chứng minh
được khả năng tổng quát hóa sang các hệ thống dịch máy chưa từng xuất
hiện trong dữ liệu huấn luyện.

## 7. Giới hạn về khả năng tái lập

Giai đoạn này xác nhận khả năng tái lập các metric Ablation Dev được
cung cấp trong cùng môi trường cục bộ và với cùng phép chia dữ liệu của
dự án.

Kết quả không chứng minh khả năng tái lập trên máy tính hoặc môi trường
độc lập khác; cũng không chứng minh khả năng tổng quát hóa sang hệ thống
dịch máy chưa thấy, cặp ngôn ngữ khác hoặc miền dữ liệu khác.

Tập Test không được sử dụng trong giai đoạn này.

## 8. Vị trí lưu bằng chứng

Thư mục kết quả trong sandbox:

`D:\MLA_Reproduction_Test\results\week10\ablation_dev\`

Đường dẫn tệp metric trong dự án gốc:

`D:\Translation-Quality-Estimation\results\week10\ablation_dev\dev_ablation_metrics.csv`

Đường dẫn tệp metric trong sandbox:

`D:\MLA_Reproduction_Test\results\week10\ablation_dev\dev_ablation_metrics.csv`

**Kết luận:** G3.5.3 hoàn thành đối với phạm vi đối chiếu các tệp metric
được cung cấp. Hai tệp CSV đã tải lên giống hệt nhau ở cấp byte; kết quả
tái lập phù hợp với các metric Ablation G2 đã ghi nhận. Cần lưu lại
đường dẫn nguồn của từng tệp để hoàn thiện bằng chứng truy xuất nguồn
gốc.
