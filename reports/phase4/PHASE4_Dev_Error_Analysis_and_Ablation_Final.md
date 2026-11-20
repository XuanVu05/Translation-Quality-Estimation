# PHASE 4 – PHÂN TÍCH LỖI, KIỂM TOÁN MQM VÀ ABLATION TRÊN DEV

**Dự án:** Second Pair of Eyes – Reference-Free Critical Error Detection  
**Học phần:** Machine Learning Applications (MLA)  
**Tập dữ liệu:** WMT 2020 MQM English–German (`newstest2020`)  
**Phạm vi báo cáo:** Chỉ sử dụng Dev; không thực hiện huấn luyện lại và không sử dụng Test cho các phân tích của Phase 4.

---

## 1. Mục tiêu và phạm vi

Phase 4 tập trung vào ba mục tiêu:

1. Phân tích các trường hợp được LR_Base xếp hạng cao nhưng không đạt nhãn Critical (false positives theo nhãn vận hành).
2. Phân tích các trường hợp Critical bị bỏ sót trong danh sách ưu tiên (false negatives).
3. Đánh giá ảnh hưởng của đặc trưng danh tính hệ thống dịch máy thông qua ablation trên Dev.

Các kết quả trong tài liệu này chỉ mô tả tập Dev. Các chỉ số Test đã được báo cáo trong phần đánh giá tổng thể của dự án và không được tính lại, điều chỉnh hoặc dùng để lựa chọn cấu hình trong Phase 4.

## 2. Quy ước nhãn và cách diễn giải

Một annotation được xem là serious nếu thỏa mãn quy tắc vận hành của dự án:

- `Severity = Major` và `category` thuộc nhóm `Accuracy/`; hoặc
- `category = Non-translation!`.

Một rater chỉ đóng góp tối đa một serious vote cho mỗi phân đoạn. Phân đoạn được gán `y_primary = 1` khi có ít nhất hai rater xác nhận lỗi serious; các trường hợp còn lại có `y_primary = 0`.

Vì vậy, `y_primary = 0` chỉ có nghĩa là phân đoạn không đạt ngưỡng đồng thuận Critical theo quy tắc trên. Nhãn 0 **không đồng nghĩa** với bản dịch hoàn toàn không có lỗi. Các annotation Minor, lỗi không thuộc nhóm được định nghĩa là serious, hoặc bất đồng giữa rater vẫn có thể tồn tại.

Trong báo cáo này, thuật ngữ *false positive* và *false negative* được dùng theo nghĩa tương đối với nhãn nhị phân vận hành, không phải phán quyết độc lập về chất lượng dịch.

## 3. Dữ liệu và cấu hình phân tích Dev

Tập Dev gồm:

| Thuộc tính | Giá trị |
|---|---:|
| Số phân đoạn hệ thống–tài liệu–câu | 1.554 |
| Nhãn âm (`y_primary = 0`) | 1.336 |
| Nhãn dương (`y_primary = 1`) | 218 |
| Tỷ lệ Critical | 14,03% |
| Số tài liệu Dev | 20 |
| Ngân sách rà soát 20% | 311 mẫu |

Cấu hình LR_Base sử dụng TF-IDF của câu nguồn và câu dịch, kết hợp 12 đặc trưng bề mặt. Các phép ablation được thực hiện trên cùng tập Dev và cùng ngân sách top-20%.

## 4. Ablation: vai trò của system identity

### 4.1. Kết quả

| Chỉ số | LR_Base | LR_Plus_System | System_Only |
|---|---:|---:|---:|
| PR-AUC | 0,1961 | 0,1991 | 0,1568 |
| Recall@20% | **0,2890** | 0,2798 | 0,2523 |
| Precision@20% | **0,2026** | 0,1961 | 0,1768 |
| Lift@20% | **1,4440** | 1,3982 | 1,2607 |
| MCC@20% | **0,0897** | 0,0805 | 0,0527 |
| Số mẫu được chọn | 311 | 311 | 311 |
| Số Critical trong top 20% | 63 | 61 | 55 |

### 4.2. Diễn giải

LR_Plus_System tăng PR-AUC nhẹ so với LR_Base (0,1991 so với 0,1961). Tuy nhiên, tại ngân sách rà soát 20%, cấu hình bổ sung system identity có Recall, Precision, Lift và MCC thấp hơn LR_Base; số mẫu Critical được đưa vào top 20% giảm từ 63 xuống 61.

System_Only có kết quả thấp hơn LR_Base ở tất cả các chỉ số được báo cáo. Điều này cho thấy chỉ sử dụng danh tính hệ thống không đủ để thay thế tín hiệu từ văn bản nguồn, bản dịch và các đặc trưng bề mặt trong thiết lập hiện tại.

### 4.3. Quyết định cấu hình

Nhóm giữ **LR_Base** làm cấu hình chính cho hệ thống. Quyết định dựa trên mục tiêu vận hành đã xác định trước: ưu tiên phát hiện Critical trong top 20% khi ngân sách rà soát cố định. Kết quả ablation chỉ là point estimates trên Dev; không có khoảng tin cậy hoặc kiểm định ý nghĩa thống kê cho chênh lệch giữa các cấu hình. Vì vậy, không kết luận rằng system identity luôn có hại hoặc không hữu ích trong mọi thiết lập.

## 5. Phân tích False Positives trên Dev

### 5.1. Quy mô và nguyên tắc kiểm toán

Trong 311 mẫu được LR_Base chọn vào top 20% trên Dev, có 248 mẫu mang nhãn `y_primary = 0`. Đây là false positives theo nhãn Critical vận hành.

Toàn bộ 248 mẫu đã được đối chiếu với MQM. Kết quả tổng hợp cho thấy:

- 248/248 mẫu có annotation MQM được đối chiếu.
- Các mẫu đều có ba rater trong lần kiểm toán này.
- Không mẫu nào đạt từ hai serious vote trở lên; nhãn tái dựng đều là 0, khớp với `y_primary`.
- Có 87 dòng annotation serious thuộc 68 phân đoạn, nhưng mỗi phân đoạn trong nhóm này chỉ có một serious vote, chưa đạt ngưỡng Critical.
- 180 mẫu ban đầu có 0/3 serious vote; 68 mẫu bổ sung có 1/3 serious vote.

Như vậy, các mẫu này là false positives đối với nhãn nhị phân theo quy tắc dự án, nhưng không thể mặc định là các bản dịch hoàn toàn không có vấn đề.

### 5.2. Annotation MQM trong nhóm 248 mẫu

Các nhóm annotation xuất hiện gồm cả lỗi Minor và những annotation không thuộc tiêu chí serious. Một số nhóm nổi bật theo số dòng annotation và số phân đoạn duy nhất:

| Nhóm/category | Số dòng annotation | Số phân đoạn duy nhất |
|---|---:|---:|
| Accuracy/Mistranslation | 506 | 159 |
| Style/Awkward | 205 | 132 |
| Fluency/Punctuation | 162 | 47 |
| Fluency/Grammar | 151 | 101 |
| Terminology/Inappropriate for context | 99 | 78 |
| Accuracy/Omission | 41 | 32 |
| Accuracy/Untranslated text | 40 | 28 |
| Accuracy/Addition | 23 | 19 |

Các số liệu trên là số dòng annotation và số phân đoạn duy nhất theo từng category; một phân đoạn có thể xuất hiện ở nhiều category. Không cộng các hàng để suy ra số phân đoạn tổng duy nhất.

Trong 68 mẫu có một serious vote, có 240 dòng annotation thuộc `Accuracy/Mistranslation` trên 67/68 mẫu. Tuy nhiên, chỉ một rater xác nhận serious ở mỗi mẫu này, nên chúng vẫn mang nhãn 0 theo ngưỡng đồng thuận.

### 5.3. Kiểm tra biến thể target

Trong 68 mẫu bổ sung, có 13 mẫu có biến thể target giữa các annotation ngay cả sau khi loại bỏ marker `<v>`; 55 mẫu còn lại thống nhất sau bước bỏ marker này.

Rà soát dữ liệu sơ bộ đối với 13 trường hợp ghi nhận:
- 6 trường hợp có khác biệt nội dung (`Content_difference`);
- 6 trường hợp có dấu hiệu dữ liệu bị lặp hoặc hỏng (`Corrupted`);
- 1 trường hợp có dấu hiệu bị cắt cụt (`Truncated`).

Đây là phân loại phục vụ kiểm toán dữ liệu, không phải kết luận chuyên gia về mức độ sai của bản dịch. Các trường hợp khác biệt target cần được diễn giải thận trọng vì có thể ảnh hưởng đến việc ghép annotation với đầu ra MT.

### 5.4. Kiểm toán định tính 10 trường hợp

Nhóm thực hiện kiểm tra sâu một mẫu có chủ đích gồm 10 trường hợp Dev được xếp hạng cao nhưng không đạt nhãn Critical. Trong bộ kiểm toán này:

- 10/10 trường hợp có đối chiếu MQM thành công;
- có 59 dòng annotation MQM được truy xuất;
- có 2 dòng mang severity Major;
- không có annotation nào thỏa điều kiện serious sau khi xét đồng thời category và severity;
- cả 10 trường hợp đều được tính lại `y_primary = 0`.

Một bộ kiểm tra 10 trường hợp khác được lưu trong thư mục `current_10_case_analysis`; bộ này có 47 dòng annotation ứng viên, trong đó 42 dòng khớp target và 5 dòng không khớp. Cả 10 trường hợp vẫn có ít nhất một annotation khớp và không có serious vote. Hai bộ 10 trường hợp được tạo theo các lựa chọn mẫu khác nhau, do đó không gộp số dòng hoặc kết quả của chúng thành một mẫu duy nhất.

Mẫu 10 trường hợp là mẫu chọn có chủ đích, không phải mẫu ngẫu nhiên và không đại diện thống kê cho toàn bộ 248 false positives. Kết quả cho thấy việc xếp hạng cao có thể phản ánh những vấn đề chất lượng khác với định nghĩa Critical, nhưng không chứng minh mọi false positive đều hữu ích cho reviewer.

## 6. Phân tích False Negatives trên Dev

### 6.1. Quy mô và xác nhận nhãn

LR_Base chọn 311/1.554 mẫu ở top 20%, trong đó có 63 Critical. Do Dev có 218 mẫu Critical, số false negatives là:

\[
FN = 218 - 63 = 155
\]

Toàn bộ 155 FN đã được đối chiếu với MQM:
- 155/155 có annotation MQM khớp;
- nhãn tái dựng khớp với nhãn ban đầu;
- tất cả có ba rater;
- 116/155 mẫu có 2/3 serious vote (74,84%);
- 39/155 mẫu có 3/3 serious vote (25,16%).

Các kết quả này xác nhận rằng FN không phải đơn thuần là lỗi thiếu annotation hoặc sai phép dựng nhãn trong tập kiểm toán.

### 6.2. Nhóm lỗi serious

| Category serious | Số dòng annotation | Số phân đoạn duy nhất |
|---|---:|---:|
| Accuracy/Mistranslation | 366 | 151 |
| Non-translation! | 19 | 16 |
| Accuracy/Untranslated text | 11 | 9 |
| Accuracy/Omission | 12 | 7 |
| Accuracy/Addition | 6 | 3 |

Một phân đoạn có thể có nhiều annotation hoặc nhiều category; vì vậy số dòng annotation không phải số phân đoạn độc lập. Accuracy/Mistranslation là nhóm chiếm ưu thế trong các FN được kiểm tra.

### 6.3. Phân bố thứ hạng của FN

| Dải thứ hạng LR_Base | Số FN | Điểm trung bình | Thứ hạng nhỏ nhất–lớn nhất |
|---|---:|---:|---:|
| 312–400 | 10 | 0,303233 | 317–400 |
| 401–800 | 57 | 0,252288 | 405–791 |
| 801–1200 | 48 | 0,186916 | 806–1188 |
| 1201–1554 | 40 | 0,103192 | 1205–1546 |
| **Tổng** | **155** | — | — |

Chỉ 10/155 FN nằm trong dải thứ hạng 312–400; 145/155 (93,55%) nằm sau thứ hạng 400. Điều này cho thấy phần lớn FN có điểm/rank thấp hơn đáng kể so với vùng đầu danh sách, dù vẫn có một số trường hợp nằm gần ranh giới top 20%.

### 6.4. Kiểm tra vùng biên top 20%

Tập kiểm tra biên gồm 11 mẫu ở thứ hạng 306–316. Điểm LR_Base giảm đơn điệu trong vùng được kiểm tra, từ 0,311303 ở hạng 306 xuống 0,309601 ở hạng 316. Không quan sát thấy điểm bằng nhau tại vùng biên trong 11 mẫu này.

Cả 11 mẫu đều có `y_primary = 0`. Vì vậy, kiểm tra này chỉ xác nhận thứ tự và không có tie trong vùng mẫu đã kiểm tra; nó không cung cấp bằng chứng về các positive bị bỏ sót ngay tại ranh giới top 20%.

### 6.5. Kiểm tra định tính 12 trường hợp FN

Nhóm chọn 12 trường hợp FN để xem xét nội dung và annotation. Mẫu gồm các trường hợp ở nhiều dải thứ hạng, từ 317 đến 1546. Người dùng đã xác nhận rằng các lỗi trong cả 12 trường hợp phù hợp với nhận định ban đầu của nhóm.

Các ví dụ được rà soát có những dạng vấn đề như thuật ngữ chuyên ngành, thực thể/tên riêng, nội dung chưa được dịch, thuật ngữ pháp lý và cấu trúc ngữ pháp–ngữ nghĩa. Kết quả này cung cấp minh họa cụ thể về những lỗi serious mà LR_Base chưa đưa vào vùng ưu tiên.

Việc xác nhận 12 trường hợp là rà soát định tính trong phạm vi nhóm, không phải expert adjudication độc lập. Không suy rộng tỷ lệ hoặc tần suất các loại lỗi trong 12 trường hợp ra toàn bộ 155 FN.

### 6.6. Phân bố FN theo hệ thống MT

| Hệ thống | Số FN |
|---|---:|
| Online-A | 31 |
| OPPO | 23 |
| Online-B | 22 |
| Tencent | 22 |
| eTranslation | 21 |
| Huoshan | 20 |
| Tohoku | 16 |

Đây là số lượng FN tuyệt đối theo hệ thống. Không diễn giải các con số này thành tỷ lệ lỗi hoặc so sánh hệ thống nào kém hơn, vì chưa chuẩn hóa theo tổng số positive của từng hệ thống.

## 7. Tổng hợp phát hiện và hàm ý

Phase 4 đưa ra bốn phát hiện chính:

1. **System identity không cải thiện mục tiêu vận hành trên Dev.** LR_Plus_System có PR-AUC nhỉnh hơn rất ít, nhưng kém LR_Base ở các chỉ số top-20%. LR_Base được giữ làm cấu hình chính.
2. **False positives không đồng nghĩa với bản dịch không có lỗi.** Các mẫu được xếp hạng cao nhưng không đạt nhãn Critical vẫn có thể có annotation Minor, bất đồng hoặc một serious vote chưa đủ ngưỡng.
3. **False negatives phần lớn nằm sâu hơn trong danh sách.** 145/155 FN có thứ hạng sau 400; các trường hợp này cho thấy mô hình còn bỏ sót nhiều phân đoạn được MQM xác nhận Critical.
4. **Điểm rủi ro nên được dùng để ưu tiên, không thay thế phán đoán con người.** Cả FP và FN đều cho thấy giới hạn của việc chuyển chất lượng dịch đa chiều thành một nhãn nhị phân duy nhất.

Với vai trò *Second Pair of Eyes*, LR_Base có thể tạo danh sách ưu tiên để reviewer bắt đầu rà soát. Tuy nhiên, Phase 4 chưa chứng minh rằng quy trình này làm giảm thời gian hậu biên tập hoặc tăng số lỗi được phát hiện trong môi trường thực tế; cần thử nghiệm với reviewer để kiểm tra tác động đó.

## 8. Giới hạn và lưu ý phương pháp

- Kết quả ablation là point estimates trên một tập Dev gồm 20 tài liệu; chưa có bootstrap CI hoặc kiểm định ý nghĩa thống kê cho chênh lệch giữa các cấu hình.
- Mẫu 10 FP và 12 FN là mẫu định tính có chủ đích, không đại diện thống kê cho toàn bộ tập.
- Xác nhận của nhóm đối với 12 FN không tương đương đánh giá độc lập của chuyên gia dịch thuật.
- Nhãn Critical là định nghĩa vận hành dựa trên category, severity và ngưỡng đồng thuận; nhãn 0 không đồng nghĩa không có lỗi.
- Một phân đoạn có thể có nhiều dòng annotation và nhiều category; cần phân biệt số dòng annotation với số phân đoạn duy nhất.
- Các thống kê theo hệ thống là số lượng tuyệt đối; không so sánh tỷ lệ nếu chưa chuẩn hóa theo số positive của từng hệ thống.
- Các kết quả trong tài liệu này không chứng minh khả năng tổng quát hóa sang cặp ngôn ngữ, miền dữ liệu hoặc hệ thống MT chưa xuất hiện.
- Không thực hiện huấn luyện lại, thay đổi nhãn hoặc đánh giá lại Test trong Phase 4.

## 9. Artefact và bằng chứng

Các artefact chính liên quan đến Phase 4 được lưu trong dự án, gồm:

**Ablation Dev**
- `results/week10/ablation_dev/dev_ablation_metrics.csv`
- `results/week10/ablation_dev/dev_ablation_predictions.csv`
- `results/week10/ablation_dev/dev_ablation_manifest.json`

**FP audit**
- `results/week11/error_analysis_dev/` – các bảng kiểm toán FP và MQM tương ứng.
- `mqm_10_cases_audit_report.txt` – báo cáo kiểm toán một bộ 10 trường hợp.
- `current_10_case_analysis/current_10_case_audit_report.md` – kiểm toán bộ 10 trường hợp hiện hành.
- `PHASE4_FP_248_Full_MQM_Audit.csv` – bảng đối chiếu 248 FP.
- `PHASE4_FP_248_Audit_Summary.csv` – tổng hợp kiểm toán 248 FP.
- `PHASE4_FP_248_Category_Summary.csv` – thống kê category của FP.
- `PHASE4_FP_13_Target_Variants_Reviewed.csv` – rà soát sơ bộ 13 biến thể target.

**FN audit**
- `fn_rank_band_summary.csv`
- `fn_serious_category_summary.csv`
- `fn_vote_distribution.csv`
- `fn_qualitative_sample_12.csv`
- `PHASE4_FN_12_Confirmation_Register.csv`

**Boundary check**
- `dev_lr_boundary_around_top20.csv`

Tên đường dẫn trên mô tả các artefact đã được ghi nhận trong quá trình kiểm toán. Khi đóng gói dự án, cần giữ nguyên đường dẫn thực tế của từng tệp trong repository và không đổi tên hoặc di chuyển dữ liệu gốc chỉ để khớp danh sách này.

## 10. Kết luận Phase 4 và trạng thái hoàn thành

Phase 4 đã hoàn thành các phân tích cần thiết trên Dev: ablation system identity, kiểm toán 248 false positives, phân tích 155 false negatives, rà soát định tính các trường hợp tiêu biểu và kiểm tra vùng biên top 20%.

Cấu hình LR_Base được giữ làm cấu hình chính vì đạt kết quả tốt hơn LR_Plus_System ở các chỉ số ưu tiên rà soát top-20% trên Dev. Phân tích FP cho thấy nhãn không-Critical có thể vẫn đi kèm vấn đề chất lượng dịch hoặc bất đồng annotation. Phân tích FN xác nhận mô hình bỏ sót 155 mẫu Critical, trong đó phần lớn nằm ngoài vùng ưu tiên đầu danh sách.

**Trạng thái: PHASE 4 – COMPLETED.**

Việc hoàn thành Phase 4 không đồng nghĩa mọi giới hạn nghiên cứu đã được giải quyết. Các vấn đề về tính đại diện của mẫu định tính, quy mô Dev, đánh giá người dùng và khả năng tổng quát hóa vẫn cần được trình bày trong báo cáo cuối kỳ. Không cần chạy lại mô hình hoặc mở lại Test để hoàn tất tài liệu Phase 4.
