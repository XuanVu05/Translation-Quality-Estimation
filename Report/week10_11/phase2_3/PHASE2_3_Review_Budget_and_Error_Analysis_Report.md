# Báo cáo tổng kết Phase 2 và Phase 3
## Second Pair of Eyes – Reference-Free Critical Error Detection

**Ngày chốt:** 19/11/2026  
**Phạm vi:** Kết quả đánh giá trên tập Test của `week10`; phân tích định tính MQM và độ tin cậy thống kê.  
**Nguyên tắc:** Không huấn luyện lại mô hình, không thay đổi nhãn, không điều chỉnh Test để lựa chọn mô hình.

---

# 1. Tóm tắt điều hành

Phase 2 và Phase 3 đã hoàn thành ở mức đủ để chuyển sang giai đoạn tiếp theo, với một số giới hạn cần được giữ nguyên khi diễn giải kết quả.

- **Phase 2:** Đã so sánh Random, Heuristic Rules, Logistic Regression (LR) và Linear SVM tại ngân sách rà soát 20%, đồng thời xem xét PR-AUC và paired document-level bootstrap.
- **Phase 3:** Đã kiểm tra tính nhất quán giữa dự đoán và nhãn MQM, phân tích phân bố phiếu 0/3–3/3, xem xét ví dụ ở ranh giới nhãn và diễn giải bootstrap theo đơn vị document.
- LR có PR-AUC cao nhất trong các phương pháp hiện có (0,1971), nhưng lợi thế Recall@20% so với Heuristic nhỏ và chưa được chứng minh rõ ràng qua khoảng tin cậy.
- Không có cơ sở để tuyên bố LR vượt trội chắc chắn ở mọi khía cạnh; cũng không có cơ sở để loại bỏ LR chỉ vì PR-AUC thấp hơn 0,5.
- Có thể chuyển sang Phase 4: đánh giá hướng cải thiện mô hình và phân tích lỗi có kiểm soát trên Development, không dùng Test để lựa chọn mô hình.

# 2. Phase 2 – So sánh mô hình theo review budget

## 2.1. Thiết lập đánh giá

Tập Test gồm 1.575 bản dịch, trong đó 162 bản dịch có nhãn lỗi nghiêm trọng theo quy tắc đa số MQM. Tỷ lệ dương tính là:

\[
\text{Prevalence} = \frac{162}{1575} \approx 10,29\%.
\]

Ngân sách rà soát 20% tương ứng:

\[
k = \lceil 0,20 \times 1575 \rceil = 315.
\]

Recall@20% là metric vận hành trọng tâm vì hệ thống được thiết kế để ưu tiên các bản dịch cần con người kiểm tra trong một ngân sách hữu hạn. PR-AUC bổ sung góc nhìn về chất lượng xếp hạng trên nhiều ngưỡng score, thay vì chỉ tại một ngưỡng top-20%.

## 2.2. Kết quả trên Test

| Phương pháp | PR-AUC | Precision@20% | Recall@20% | Lift@20% | MCC@20% |
|---|---:|---:|---:|---:|---:|
| Random | 0,1091 | 0,1016 | 0,1975 | 0,9877 | -0,0021 |
| Heuristic Rules | 0,1391 | 0,1587 | 0,3086* | 1,5432 | 0,0920 |
| Logistic Regression | **0,1971** | **0,1619** | **0,3148** | **1,5741** | **0,0972** |
| Linear SVM | 0,1676 | 0,1206 | 0,2346 | 1,1728 | 0,0293 |

`*` Kết quả top-315 Heuristic ban đầu chịu ảnh hưởng của hòa điểm tại ngưỡng 0,8; cần đọc cùng phân tích tie ở mục 2.3. Các số liệu trong bảng là kết quả đã lưu, không phải kết quả của một lần chạy mô hình mới.

LR có PR-AUC cao nhất trong bốn phương pháp. PR-AUC 0,1971 cao hơn prevalence 0,1029 và các baseline được báo cáo. Đây là tín hiệu có ích, nhưng không nên dùng một ngưỡng PR-AUC phổ quát như 0,5 hoặc 0,9 để kết luận mô hình đạt hay không đạt. PR-AUC phụ thuộc tỷ lệ lớp, dữ liệu, cách tính Average Precision và mục tiêu ứng dụng.

## 2.3. Hòa điểm trong Heuristic Rules

Điểm Heuristic tại ranh giới top-20% không tạo ra thứ tự duy nhất:

- 276 bản dịch có score lớn hơn 0,8.
- 132 bản dịch có score đúng bằng 0,8.
- Cần chọn thêm 39 bản dịch trong nhóm 132 bản dịch đồng điểm để đủ 315.

Trong nhóm score lớn hơn 0,8 có 47 nhãn dương tính; trong nhóm score bằng 0,8 có 9 nhãn dương tính. Vì vậy, số dương tính được chọn bởi Heuristic phụ thuộc vào quy tắc phá hòa:

| Cách chọn 39 trường hợp đồng điểm | Số dương tính trong top-315 | Recall@20% |
|---|---:|---:|
| Biên dưới: chọn các trường hợp không dương tính trước | 47 | 29,01% |
| Kỳ vọng nếu lấy ngẫu nhiên trong nhóm hòa điểm | 49,66 | 30,65% |
| Biên trên: chọn các trường hợp dương tính trước | 56 | 34,57% |

LR tìm được 51/162 trường hợp dương tính trong top-315, Recall@20% = 31,48%. Kết quả LR cao hơn kỳ vọng ngẫu nhiên của Heuristic khoảng 0,83 điểm phần trăm, nhưng nằm trong khoảng khả dĩ của Heuristic khi phá hòa. Do đó, không được diễn giải chênh lệch top-20% ban đầu là bằng chứng chắc chắn rằng LR tốt hơn Heuristic về Recall@20%.

Trong báo cáo nghiên cứu, cần công bố rõ quy tắc phá hòa của Heuristic (ví dụ: thứ tự khóa ổn định được định trước hoặc lấy trung bình qua nhiều lần chọn ngẫu nhiên). Không được chọn cách phá hòa sau khi xem nhãn Test.

## 2.4. Paired document-level bootstrap: LR so với Heuristic

Chênh lệch được định nghĩa là metric(LR) trừ metric(Heuristic). Kết quả 1.000 lần paired document-cluster bootstrap:

| Metric | Chênh lệch LR − Heuristic | Khoảng tin cậy 95% |
|---|---:|---:|
| PR-AUC | +0,057971 | [0,015118; 0,123220] |
| Recall@20% | +0,006173 | [-0,088002; 0,181829] |
| Precision@20% | +0,003175 | [-0,052483; 0,082039] |
| Lift@20% | +0,030864 | [-0,439306; 0,907456] |
| MCC@20% | +0,005225 | [-0,079792; 0,137567] |

Diễn giải:

- Khoảng tin cậy PR-AUC không chứa 0: trong bootstrap hiện tại, chênh lệch PR-AUC nghiêng về LR.
- Khoảng tin cậy của Recall@20%, Precision@20%, Lift@20% và MCC@20% đều chứa 0: chưa có bằng chứng đủ rõ để kết luận LR cải thiện các metric này so với Heuristic.
- Kết quả này phù hợp với mục tiêu vận hành: LR có chất lượng xếp hạng tổng thể tốt hơn theo PR-AUC, trong khi lợi thế tại một ngân sách 20% chưa chắc chắn.

Các phép so sánh paired khác cũng đã được lưu:
- LR − SVM: PR-AUC +0,028476, CI [-0,009450; 0,092583].
- Heuristic − SVM: PR-AUC -0,030082, CI [-0,076359; 0,016666].

Không nên khẳng định các chênh lệch trên có ý nghĩa thống kê khi khoảng tin cậy vẫn chứa 0.

## 2.5. PR-AUC và Recall@20% trả lời hai câu hỏi khác nhau

- **Recall@20%:** Với đúng 20% ngân sách kiểm duyệt, hệ thống tìm được bao nhiêu phần trăm tổng số lỗi nghiêm trọng?
- **PR-AUC / Average Precision:** Khi thay đổi ngưỡng score, mô hình duy trì quan hệ precision–recall như thế nào trên toàn bộ dải ngưỡng?

Vì vậy, PR-AUC không thay thế Recall@20%. Trong bài toán Second Pair of Eyes, Recall@20% là metric gắn trực tiếp với quyết định phân bổ nguồn lực; PR-AUC là metric bổ sung để đánh giá chất lượng xếp hạng tổng quát.

# 3. Phase 3 – Kiểm tra nhãn, phân tích ranh giới và độ tin cậy

## 3.1. Đối chiếu dự đoán với MQM

File `test_predictions_with_mqm.csv` có 1.575 bản dịch thuộc 20 document và 7 hệ thống dịch. Đối chiếu cho thấy:

- `mqm_match = True`: 1.575/1.575.
- `label_match = True`: 1.575/1.575.

Nghĩa là số phiếu lỗi nghiêm trọng và nhãn đa số tái dựng từ thông tin MQM trong file khớp với các trường đã lưu. Đây là kiểm tra nhất quán nội bộ giữa file dự đoán và dữ liệu MQM được ghép vào file; không nên mở rộng kết luận này thành khẳng định rằng toàn bộ lịch sử sử dụng Test đã được kiểm chứng.

## 3.2. Phân bố phiếu đánh giá

Mỗi bản dịch có 3 lượt đánh giá. Quy tắc nhãn đa số là `y_primary = 1` khi có ít nhất 2/3 phiếu lỗi nghiêm trọng.

| Số phiếu nghiêm trọng | Số bản dịch | Nhãn cuối |
|---|---:|---:|
| 0/3 | 1.092 | 0 |
| 1/3 | 321 | 0 |
| 2/3 | 95 | 1 |
| 3/3 | 67 | 1 |
| **Tổng** | **1.575** | |

Có 416/1.575 bản dịch (26,41%) nằm ở hai nhóm 1/3 và 2/3. Đây là các trường hợp không có sự nhất trí tuyệt đối giữa cả ba lượt đánh giá. Cần gọi đây là nhóm có phiếu đánh giá không nhất trí tuyệt đối, không nên gọi toàn bộ chúng là lỗi gán nhãn.

## 3.3. Ví dụ ở ranh giới nhãn

**Trường hợp 1/3 – nhãn âm tính**

- Hệ thống: `eTranslation.737`.
- Document: `reuters.276668`; `doc_id=2`; `seg_id=858`.
- Số phiếu nghiêm trọng: 1/3; `y_primary=0`.
- Điểm LR: 0,6415.
- Các nhóm lỗi được ghi nhận gồm Accuracy/Mistranslation, Accuracy/Omission, Fluency/Grammar và Style/Awkward.

Trường hợp này cho thấy LR có thể xếp hạng cao một bản dịch không đạt ngưỡng nhãn đa số. Một phần tín hiệu mà mô hình học được có thể liên quan đến hiện tượng lỗi nhẹ hoặc vấn đề chất lượng dịch nói chung, chứ không chỉ lỗi nghiêm trọng theo định nghĩa nhị phân.

**Trường hợp 2/3 – nhãn dương tính**

- Hệ thống: `Online-A.1574`.
- Document: `abcnews.364021`; `doc_id=1`; `seg_id=1033`.
- Source: “Greece: 5 deny poor women's babies sold in illegal adoptions”
- Target: “Griechenland: 5 leugnen arme Frauenbabys, die in illegalen Adoptionen verkauft werden”
- Số phiếu nghiêm trọng: 2/3; `y_primary=1`.
- Điểm LR: 0,1079.
- Nhóm lỗi: Accuracy/Mistranslation.

Đây là ví dụ LR cho điểm thấp đối với một bản dịch có nhãn dương tính, tức một trường hợp bị bỏ sót nếu không nằm trong ngân sách rà soát.

Hai ví dụ minh họa sự không trùng khớp tuyệt đối giữa điểm mô hình và nhãn đa số. Chúng không đủ để đại diện cho toàn bộ lỗi của LR; cần đặt trong thống kê tổng thể ở mục tiếp theo.

## 3.4. Phân tích các trường hợp LR ưu tiên và bỏ sót

Trong 315 bản dịch thuộc Top 20% LR:

| Số phiếu MQM | Top 20% LR | Ngoài Top 20% LR |
|---:|---:|---:|
| 0/3 | 184 | 908 |
| 1/3 | 80 | 241 |
| 2/3 | 35 | 60 |
| 3/3 | 16 | 51 |
| **Tổng** | **315** | **1.260** |

LR phát hiện 51/162 nhãn dương tính, Recall@20% = 31,48%. Trong Top 20%, có 80 trường hợp 1/3 phiếu. Theo quy tắc nhãn đa số, đây là false positive; tuy nhiên, không thể kết luận chúng hoàn toàn không có lỗi vì một annotator đã ghi nhận lỗi nghiêm trọng.

Ngoài ngân sách rà soát còn 111/162 trường hợp dương tính, gồm 60 trường hợp 2/3 và 51 trường hợp 3/3. Việc bỏ sót một số trường hợp được cả ba annotator xác nhận là lỗi nghiêm trọng là điểm cần tập trung trong phân tích lỗi và cải thiện mô hình.

**Giới hạn:** Các con số trên là phân tích theo nhãn đa số và thứ hạng LR tại ngân sách 20%; chúng không tự giải thích nguyên nhân ngôn ngữ học của từng lỗi. Cần kiểm tra source, target và MQM spans trước khi đưa ra kết luận về loại lỗi mô hình khó phát hiện.

## 3.5. Diễn giải document-level bootstrap

Tập Test có 20 document. Trong document-level bootstrap, document là đơn vị lấy mẫu vì các bản dịch trong cùng một document có thể phụ thuộc vào ngữ cảnh và đặc điểm văn bản chung.

Quy trình paired bootstrap:

1. Lấy ngẫu nhiên 20 document từ 20 document Test, có hoàn lại.
2. Với mỗi document được lấy, giữ toàn bộ bản dịch thuộc document đó; không lấy từng segment độc lập.
3. Tính metric của LR và Heuristic trên cùng mẫu document.
4. Tính chênh lệch LR − Heuristic.
5. Lặp lại 1.000 lần; lấy các phân vị 2,5% và 97,5% của phân phối chênh lệch làm khoảng tin cậy bootstrap 95%.

Dùng cùng một mẫu document cho cả hai mô hình giúp phép so sánh có tính paired và giảm ảnh hưởng của việc hai mô hình được đánh giá trên những tập document khác nhau.

**Giới hạn diễn giải:** Chỉ có 20 cụm document độc lập ở Test. Khoảng tin cậy phản ánh biến động theo cách lấy mẫu document trong tập đánh giá này, nhưng độ ổn định của ước lượng còn hạn chế khi số cụm nhỏ. Bootstrap không chứng minh khả năng tổng quát hóa trên mọi miền văn bản hoặc mọi hệ thống dịch. Khoảng tin cậy cũng không khắc phục được vấn đề nếu Test đã từng được dùng lặp lại để lựa chọn mô hình.

## 3.6. Những gì Phase 3 đã và chưa chứng minh

Đã thực hiện:
- Đối chiếu số phiếu MQM và nhãn đa số với file dự đoán.
- Thống kê phân bố 0/3, 1/3, 2/3, 3/3.
- Kiểm tra ví dụ 1/3 và 2/3.
- Phân tích thành phần Top 20% và các trường hợp dương tính bị bỏ sót.
- Diễn giải đơn vị lấy mẫu, cách ghép cặp và giới hạn của document-level bootstrap.

Chưa được chứng minh:
- Chưa xác định nguyên nhân ngôn ngữ học cho toàn bộ 111 trường hợp dương tính bị LR bỏ sót.
- Chưa kiểm toán độc lập toàn bộ lịch sử sử dụng Test trước khi khóa split.
- Không thể suy ra độ tin cậy ngoài miền dữ liệu chỉ từ 20 document Test.
- Chưa dùng phân tích định tính để chứng minh mô hình mới sẽ cải thiện; điều đó cần được kiểm tra trên Dev.

# 4. Phân biệt Test analysis và week11 Development error analysis

Tài liệu mô tả thư mục `results/week11/error_analysis_dev/` là phân tích định tính trên **Development**, tập trung vào false positive: các bản dịch thuộc Top 20% LR nhưng có `y=0`. Tài liệu liệt kê:
- Các file tổng thể Top 20%, summary, status summary và rater detail.
- Danh sách annotation không khớp target variant.
- Bộ 10 trường hợp chính và các báo cáo kiểm toán MQM, annotated spans, ngữ cảnh câu lân cận, đối chiếu bản dịch gốc.
- Một bộ 10 trường hợp đa dạng theo document.

Đây là nguồn phân tích định tính có giá trị cho Phase 4, nhưng phải giữ ranh giới dữ liệu:
- Phân tích Test trong báo cáo này dùng để báo cáo đánh giá cuối cùng; không dùng để điều chỉnh mô hình.
- Phân tích false positive trên Dev có thể dùng để hình thành giả thuyết, thiết kế đặc trưng hoặc thay đổi mô hình trong Phase 4.
- Không gộp các số liệu Dev (ví dụ 180 trường hợp) vào mẫu số Test (1.575 bản dịch).
- Các nhận xét trong bộ 10 case Dev chỉ là bằng chứng định tính cho những trường hợp đã chọn, không phải ước lượng tỷ lệ lỗi trên toàn bộ tập dữ liệu.

Theo mô tả tài liệu week11, nhiều false positive trên Dev không phải dự đoán hoàn toàn vô căn cứ: một số bản dịch có lỗi Minor về Fluency, Style hoặc Accuracy, hoặc có lỗi Major thuộc danh mục không nằm trong định nghĩa Critical Error. Điều này gợi ý mô hình có thể đang học tín hiệu chất lượng dịch rộng hơn nhãn Critical Error. Đây là giả thuyết cần được kiểm tra có hệ thống, không phải kết luận nhân quả.

# 5. Kết luận và quyết định chuyển giai đoạn

**Phase 2: hoàn thành.** Đã có so sánh baseline và mô hình, đánh giá tại review budget 20%, xử lý diễn giải hòa điểm Heuristic, và paired bootstrap giữa các phương pháp.

**Phase 3: hoàn thành ở mức báo cáo đánh giá và kiểm tra nhất quán.** Đã có kiểm tra MQM, phân tích ranh giới nhãn và diễn giải độ tin cậy. Phân tích sâu nguyên nhân của toàn bộ false negative chưa hoàn tất, nhưng được chuyển thành nhiệm vụ phân tích lỗi trên Dev ở Phase 4 để tránh dùng Test cho model development.

**Quyết định:** Chuyển sang Phase 4 – Model Improvement & Development Error Analysis.

# 6. Kế hoạch Phase 4

1. Kiểm tra các kết quả week11 trên Dev, đặc biệt 180 false positive trong Top 20% và bộ 10 case đã kiểm toán.
2. Phân loại nguyên nhân false positive: lỗi Minor, lỗi Major ngoài định nghĩa Critical, bất đồng annotator, tín hiệu phong cách/fluency, target variant hoặc lỗi ghép dữ liệu.
3. Phân tích false negative trên Dev bằng cùng định nghĩa nhãn và cùng review budget; ưu tiên xem các trường hợp 3/3 phiếu nhưng score thấp.
4. Từ kết quả định tính, hình thành giả thuyết cải thiện đặc trưng hoặc mô hình cổ điển; chỉ thử nghiệm và lựa chọn trên Train/Dev.
5. Giữ nguyên Test và các kết quả Test đã lưu. Chỉ đánh giá Test lại khi đã chốt thiết kế cuối cùng và có lý do phương pháp luận rõ ràng; ghi nhận minh bạch mọi lần sử dụng trước đó.
6. So sánh mô hình mới với LR_Base bằng Recall@20%, PR-AUC và các metric phụ; báo cáo chênh lệch cùng độ bất định.

---

## 7. Tài liệu và artifact liên quan

Các artifact đã được dùng hoặc được nhắc đến trong quá trình tổng kết:

- `test_predictions.csv`
- `paired_difference_ci.csv`
- `test_predictions_with_mqm.csv`
- `test_point_metrics.csv`
- `test_metrics_with_ci.csv`
- `test_audit_notes.md`
- `results/week11/error_analysis_dev/` và các báo cáo G4.1/G4.2 được mô tả trong tài liệu week11.

**Lưu ý tái lập:** Báo cáo này tổng hợp các kết quả đã lưu và các phép đối chiếu đã thực hiện trong phiên làm việc. Không chạy lại mô hình hay tái tạo bootstrap trong quá trình tạo báo cáo. Khi đưa vào repository, cần kiểm tra tên file thực tế và lưu kèm phiên bản artifact tương ứng.
