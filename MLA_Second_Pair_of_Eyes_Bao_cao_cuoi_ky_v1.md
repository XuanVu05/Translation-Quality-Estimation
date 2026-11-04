# SECOND PAIR OF EYES: PHÁT HIỆN LỖI DỊCH THUẬT NGHIÊM TRỌNG KHÔNG CẦN BẢN DỊCH THAM CHIẾU BẰNG CÁC MÔ HÌNH HỌC MÁY CỔ ĐIỂN

**Báo cáo cuối kỳ – Machine Learning Applications (MLA)**  
**Nhóm:** Group 02 – CLC02  
**Thành viên:**
Vũ Thị Xuân - 2301140104
Lê Như Quỳnh - 2301140084
Trần Nam Sơn - 2301140089
**Giảng viên hướng dẫn:** Bùi Quốc Khánh

---

## TÓM TẮT

Báo cáo trình bày quá trình xây dựng và đánh giá một hệ thống hỗ trợ ưu tiên rà soát lỗi dịch máy có tên **Second Pair of Eyes**. Hệ thống hướng tới bài toán phát hiện lỗi dịch thuật nghiêm trọng không cần bản dịch tham chiếu (_Reference-Free Critical Error Detection – CED_) cho cặp ngôn ngữ Anh–Đức. Thay vì thay thế người đánh giá hoặc tự động đưa ra kết luận cuối cùng về chất lượng bản dịch, hệ thống tạo điểm rủi ro và xếp hạng các phân đoạn dịch máy để người rà soát có thể tập trung nguồn lực vào những trường hợp có nguy cơ cao hơn trong điều kiện ngân sách kiểm tra hữu hạn.

Thực nghiệm sử dụng dữ liệu WMT 2020 MQM English–German (`newstest2020`). Sau bước tổng hợp ở cấp phân đoạn hệ thống–tài liệu–câu, tập dữ liệu gồm 9.926 mẫu thuộc 130 tài liệu và 7 hệ thống dịch máy. Nhóm xây dựng nhãn Critical theo định nghĩa vận hành: một phân đoạn được gán nhãn dương khi ít nhất hai người gán nhãn xác nhận lỗi nghiêm trọng, trong đó lỗi nghiêm trọng là lỗi có mức độ `Major` thuộc nhóm `Accuracy/` hoặc lỗi thuộc danh mục `Non-translation!`. Theo quy tắc này, tập dữ liệu có 1.183 mẫu Critical, tương đương 11,92%.

Nhóm so sánh xếp hạng ngẫu nhiên, bộ luật heuristic, Logistic Regression và Linear SVM. Các mô hình học máy sử dụng biểu diễn TF-IDF của văn bản nguồn và bản dịch đích kết hợp 12 đặc trưng bề mặt; mất cân bằng lớp được xử lý bằng trọng số lớp cân bằng. Dữ liệu được chia theo tài liệu thành Train (90 tài liệu), Dev (20 tài liệu) và Test (20 tài liệu), nhằm hạn chế rò rỉ giữa các phân đoạn thuộc cùng một tài liệu.

Trên Dev, Logistic Regression đạt PR-AUC cao nhất (0,1961), trong khi Heuristic Rules tốt hơn ở cả bốn chỉ số top-20%. Trên Test, Logistic Regression đạt PR-AUC 0,1971, cao nhất trong bốn phương pháp được báo cáo; Heuristic Rules đạt 0,1391, Linear SVM đạt 0,1676 và Random đạt 0,1091. Chênh lệch PR-AUC giữa Logistic Regression và Heuristic Rules là 0,0580, với khoảng tin cậy bootstrap theo cụm tài liệu 95% là [0,0151; 0,1232]. Tuy nhiên, khi giới hạn ngân sách rà soát ở 20% (315/1.575 mẫu), Logistic Regression phát hiện 51 mẫu Critical, chỉ nhiều hơn một mẫu so với Heuristic Rules (50 mẫu). Các khoảng tin cậy của chênh lệch ở những chỉ số vận hành tại ngân sách cố định đều bao gồm 0. Vì vậy, kết quả cho thấy Logistic Regression có khả năng xếp hạng tổng thể tốt hơn theo PR-AUC trong phép đánh giá này, nhưng chưa chứng minh được ưu thế vận hành rõ ràng so với heuristic tại ngưỡng rà soát 20%.

Phân tích lỗi trên Dev cho thấy các mẫu có điểm rủi ro cao nhưng không nhận phiếu serious theo định nghĩa vận hành vẫn có thể mang lỗi MQM không nghiêm trọng, có bất đồng giữa người gán nhãn hoặc gặp vấn đề khớp bản dịch. Kết quả nhấn mạnh rằng điểm rủi ro cần được sử dụng như tín hiệu hỗ trợ ưu tiên, không phải phán quyết chất lượng. Báo cáo cũng thảo luận các giới hạn về định nghĩa nhãn, quy mô Test, mức độ mất cân bằng, lịch sử tiếp xúc với Test, phạm vi ngôn ngữ và khả năng tái lập.

**Từ khóa:** Machine Translation Quality Estimation; Reference-Free; Critical Error Detection; MQM; Logistic Regression; Linear SVM; PR-AUC; Human-in-the-loop.

---

# 1. GIỚI THIỆU

## 1.1. Bối cảnh

Dịch máy (Machine Translation – MT) ngày càng được sử dụng trong các quy trình xử lý nội dung đa ngôn ngữ. Tuy nhiên, chất lượng đầu ra không đồng đều: một bản dịch có thể đọc trôi chảy nhưng vẫn làm sai lệch thông tin quan trọng, bỏ sót nội dung hoặc truyền đạt một ý nghĩa khác với văn bản nguồn. Trong những quy trình mà hậu quả của lỗi dịch có thể đáng kể, việc chỉ dựa vào đánh giá tổng thể hoặc kiểm tra ngẫu nhiên không phải lúc nào cũng đáp ứng được yêu cầu kiểm soát chất lượng.

Đánh giá thủ công toàn bộ đầu ra MT có thể tốn thời gian và nguồn lực. Vấn đề thực tế vì thế không chỉ là xác định bản dịch nào có lỗi, mà còn là quyết định **nên kiểm tra bản dịch nào trước** khi thời gian rà soát bị giới hạn. Đây là góc tiếp cận của dự án: xây dựng một công cụ hỗ trợ xếp hạng rủi ro để người đánh giá ưu tiên các phân đoạn có khả năng chứa lỗi nghiêm trọng.

Trong lĩnh vực đánh giá chất lượng dịch máy, _Quality Estimation_ (QE) nghiên cứu việc ước lượng chất lượng đầu ra MT mà không nhất thiết cần một bản dịch tham chiếu. Các nhiệm vụ QE ở cấp câu, cấp từ và phát hiện lỗi chi tiết đã được đưa vào những kỳ WMT Shared Task [1], [2], [3], [4]. Điều này cho thấy việc đánh giá chất lượng không tham chiếu có ý nghĩa trong các tình huống mà bản dịch tham chiếu không sẵn có tại thời điểm vận hành.

## 1.2. Phát biểu bài toán

Dự án tập trung vào bài toán **Reference-Free Critical Error Detection** cho dịch máy Anh–Đức. Đầu vào của hệ thống gồm câu nguồn tiếng Anh và câu dịch máy tiếng Đức. Hệ thống không sử dụng bản dịch tham chiếu để tính đặc trưng đầu vào. Đầu ra là một điểm rủi ro hoặc thứ hạng cho từng phân đoạn; các phân đoạn được xếp hạng cao hơn sẽ được đưa lên đầu hàng đợi rà soát.

Cần phân biệt bài toán này với phân loại nhị phân thuần túy. Trong kịch bản sử dụng dự kiến, người dùng có một ngân sách kiểm tra cố định, chẳng hạn chỉ có thể rà soát 20% tổng số phân đoạn. Do đó, một mô hình hữu ích cần ưu tiên đưa được nhiều trường hợp Critical vào phần đầu danh sách, thay vì chỉ tối ưu độ chính xác tại một ngưỡng phân loại tùy ý. Vì vậy, nhóm đánh giá cả khả năng xếp hạng tổng thể và hiệu quả tại ngân sách rà soát cố định.

## 1.3. Khoảng trống nghiên cứu và động cơ

Các hệ thống QE hiện đại có thể dựa vào mô hình ngôn ngữ tiền huấn luyện hoặc kiến trúc học sâu. Tuy nhiên, trong phạm vi học phần và điều kiện triển khai của dự án, nhóm lựa chọn khảo sát một hướng tiếp cận gọn nhẹ hơn: các mô hình học máy cổ điển, sử dụng đặc trưng văn bản và đặc trưng bề mặt, có thể huấn luyện và chạy trên CPU.

Khoảng trống mà dự án hướng tới được diễn đạt có chủ đích ở phạm vi hẹp: **xây dựng và đánh giá một baseline học máy cổ điển, có thể chạy trên CPU, cho nhiệm vụ xếp hạng lỗi dịch nghiêm trọng không cần bản dịch tham chiếu trên dữ liệu WMT 2020 MQM Anh–Đức, đồng thời so sánh với baseline ngẫu nhiên và heuristic dưới ngân sách rà soát cố định**. Dự án không tuyên bố đây là hướng tiếp cận đầu tiên, cũng không khẳng định các mô hình cổ điển có thể thay thế những phương pháp QE hiện đại.

Động cơ thứ hai là tính giải thích và khả năng kiểm toán. Một hệ thống ưu tiên rà soát cần được đánh giá không chỉ bằng một con số tổng hợp mà còn bằng việc xem xét các trường hợp được xếp hạng cao, đặc biệt là những trường hợp không được gán nhãn Critical. Việc kiểm tra các trường hợp này giúp làm rõ sự khác biệt giữa “không có phiếu serious theo quy tắc nhãn” và “bản dịch hoàn toàn không có vấn đề”.

## 1.4. Mục tiêu nghiên cứu

Dự án có bốn mục tiêu chính:

1. Xây dựng định nghĩa nhãn Critical có thể vận hành từ dữ liệu MQM nhiều người gán nhãn.
2. Xây dựng pipeline reference-free sử dụng văn bản nguồn, bản dịch máy và các đặc trưng bề mặt; hạn chế rò rỉ thông tin nhãn vào đầu vào mô hình.
3. So sánh Logistic Regression và Linear SVM với xếp hạng ngẫu nhiên và bộ luật heuristic bằng các chỉ số phù hợp với dữ liệu mất cân bằng và kịch bản rà soát theo ngân sách.
4. Phân tích các trường hợp được xếp hạng cao nhưng không đạt nhãn Critical nhằm hiểu rõ hơn giới hạn của mô hình và vai trò của người rà soát.

## 1.5. Câu hỏi nghiên cứu

Báo cáo sử dụng các câu hỏi nghiên cứu sau:

- **RQ1:** Làm thế nào xây dựng nhãn Critical theo định nghĩa vận hành từ các chú giải MQM có nhiều người gán nhãn?
- **RQ2:** Các mô hình học máy cổ điển có thể xếp hạng lỗi dịch nghiêm trọng hiệu quả đến mức nào so với baseline ngẫu nhiên và heuristic?
- **RQ3:** Việc bổ sung danh tính hệ thống dịch máy ảnh hưởng như thế nào đến kết quả trên tập Dev, đặc biệt khi mục tiêu là ưu tiên rà soát trong ngân sách cố định?
- **RQ4:** Những vấn đề chất lượng dịch và bất định trong chú giải nào xuất hiện ở các dự đoán được xếp hạng cao nhưng không đạt nhãn Critical?

## 1.6. Phạm vi và đóng góp

Phạm vi thực nghiệm giới hạn ở dữ liệu WMT 2020 MQM English–German (`newstest2020`) và bảy hệ thống dịch máy trong tập dữ liệu tổng hợp của dự án. Hệ thống được đánh giá như công cụ hỗ trợ người rà soát, không phải bộ đánh giá tự động thay thế con người.

Các đóng góp thực nghiệm của dự án gồm: (i) một quy trình tổng hợp nhãn Critical dựa trên category, severity và đồng thuận nhiều người gán nhãn; (ii) một thiết lập đánh giá theo tài liệu để giảm rò rỉ giữa các phân đoạn cùng tài liệu; (iii) so sánh các mô hình cổ điển với random và heuristic; và (iv) kiểm toán MQM định lượng kết hợp phân tích định tính các trường hợp Dev được xếp hạng cao nhưng không đạt nhãn Critical. Đây là các đóng góp trong phạm vi dự án học phần, không được diễn giải thành đóng góp mới mang tính phổ quát cho toàn bộ lĩnh vực QE.

---

# 2. CƠ SỞ LÝ THUYẾT VÀ CÔNG TRÌNH LIÊN QUAN

## 2.1. Reference-free Machine Translation Quality Estimation

Quality Estimation (QE) nghiên cứu việc ước lượng chất lượng đầu ra dịch máy mà không cần sử dụng bản dịch tham chiếu tại thời điểm dự đoán. Trong thiết lập reference-free, mô hình thường khai thác văn bản nguồn và bản dịch máy để dự đoán chất lượng ở cấp câu, cấp từ hoặc cấp đoạn lỗi. WMT 2023 tiếp tục phát triển QE theo hướng dự đoán chất lượng ở cấp câu và từ, đồng thời mở rộng nhiệm vụ phát hiện lỗi chi tiết dựa trên chú giải MQM [1]. Deoghare et al. (2023) nghiên cứu học đa nhiệm cho dự đoán QE ở cấp câu và từ; Geng et al. (2023) kết hợp dự đoán cấp từ với phát hiện error span cho cặp Anh–Đức, sử dụng XLM-R và dữ liệu pseudo-MQM [3], [4].

Các hướng nghiên cứu trên cho thấy QE không chỉ là dự đoán một điểm chất lượng tổng hợp. Việc mở rộng sang cấp từ và span giúp hệ thống chỉ ra vị trí và loại lỗi, nhưng thường đòi hỏi mô hình biểu diễn ngôn ngữ sâu và dữ liệu huấn luyện chuyên biệt. Sindhujan et al. (2025) tổng quan và so sánh các phương pháp reference-less QE trong bối cảnh hạn chế tài nguyên, bao gồm mô hình encoder và decoder [17]. Công trình này phù hợp để đặt bài toán của dự án trong bức tranh QE hiện đại, nhưng không phải bằng chứng trực tiếp cho hiệu quả của các mô hình tuyến tính được sử dụng ở đây.

Năm 2026, WMT chuyển sang đánh giá nhiều góc nhìn của chất lượng dịch ở cấp phân đoạn, gồm phát hiện error span, dự đoán điểm chất lượng liên tục và nhận diện bản dịch không lỗi. Báo cáo tổng kết WMT26 cho thấy các phương pháp LLM-as-a-judge không giám sát có kết quả cạnh tranh mạnh trong thiết lập shared task [2]. Điều này phản ánh xu hướng hiện đại của lĩnh vực; đồng thời, nó làm rõ vị trí hẹp hơn của nghiên cứu hiện tại: đánh giá baseline học máy cổ điển, nhẹ và có thể chạy trên CPU, chứ không cạnh tranh trực tiếp với các hệ thống LLM hoặc neural metric.

## 2.2. Fine-grained Error Detection và MQM

MQM là khung đánh giá chất lượng dịch theo hướng phân tích, trong đó lỗi được mô tả bằng loại lỗi và mức độ nghiêm trọng. Typology của MQM tổ chức các nhóm lỗi theo cấu trúc phân cấp; nhóm Accuracy bao gồm những lỗi làm thay đổi, thêm hoặc bỏ nội dung so với văn bản nguồn [13]. Nghiên cứu của Freitag et al. (2021) sử dụng chú giải MQM từ các dịch giả chuyên nghiệp trên đầu ra WMT 2020 và công bố dữ liệu để phục vụ nghiên cứu đánh giá MT [12]. Kho dữ liệu công khai `google/wmt-mqm-human-evaluation` chứa tệp MQM được sử dụng trong dự án [16].

Các mô hình QE dự đoán điểm câu có thể cho biết một bản dịch có vấn đề, nhưng không nhất thiết chỉ ra lỗi nằm ở đâu hoặc thuộc loại nào. Guerreiro et al. (2024) đề xuất xCOMET, kết hợp đánh giá cấp câu với phát hiện và phân loại error span, đồng thời khảo sát khả năng nhận diện lỗi cục bộ nghiêm trọng và hallucination [5]. Tại WMT26, FACET phân rã đánh giá thành Fluency, Accuracy và Consistency, với loại ngữ cảnh khác nhau cho từng nhóm lỗi [6]. Các công trình này củng cố tầm quan trọng của việc phân tích lỗi theo nhiều chiều, nhưng khác với dự án hiện tại về kiến trúc và mức độ phức tạp.

Chất lượng chú giải cũng là một nguồn bất định. Riley et al. (2026) nghiên cứu quy trình MQM re-annotation, trong đó người đánh giá rà soát và chỉnh sửa các annotation trước đó; tác giả báo cáo quy trình hai giai đoạn có thể phát hiện những lỗi bị bỏ sót ở lượt đầu [9]. Siani (2026) xem các mô hình LLM như những annotator có thể sai và xây dựng quy trình tổng hợp phán đoán về error span trong thiết lập reference-free [7]. Những công trình này liên quan đến vấn đề bất đồng và độ tin cậy của chú giải, nhưng không có nghĩa rằng nhãn vận hành của dự án có thể được thay thế trực tiếp bằng kết quả của các phương pháp đó.

## 2.3. Reference-free QE, omission và giới hạn của tín hiệu đầu vào

Một thách thức của reference-free QE là có những lỗi không để lại dấu hiệu rõ ràng trong văn bản đích. Silchenko (2026) xây dựng bộ kiểm tra đối chứng QEbreak để khảo sát bất đối xứng giữa omission và addition. Kết quả của nghiên cứu cho thấy các metric được khảo sát có xu hướng phạt omission chưa đủ mạnh; hiện tượng này cũng xuất hiện ở các metric neural có reference, dù mức độ có thể khác nhau [8]. Vì vậy, không nên diễn giải kết quả này như bằng chứng rằng chỉ các hệ thống reference-free mới gặp vấn đề omission.

Phát hiện trên có liên quan đến giới hạn của các đặc trưng bề mặt trong dự án. Độ dài, số chữ số, token lặp và chỉ báo bản dịch rỗng có thể nhận diện một số bất thường, nhưng không đủ để xác định mọi trường hợp bỏ sót hoặc sai lệch ngữ nghĩa. Do đó, mô hình cần được đánh giá bằng phân tích lỗi và không nên xem điểm rủi ro là kết luận cuối cùng về chất lượng.

## 2.4. Ranking, ưu tiên rà soát và human-in-the-loop

Trong quy trình hậu biên tập, QE có thể được dùng để xác định những phân đoạn cần chú ý. Liu et al. (2025) khảo sát việc tích hợp QE vào quy trình Machine Translation Post-Editing và báo cáo tác động tích cực đến thời gian hậu biên tập trong thiết lập nghiên cứu của họ, đồng thời lưu ý rằng QE không chính xác có thể cản trở quy trình [10]. Kết quả này hỗ trợ cách tiếp cận xem QE như công cụ hỗ trợ công việc, nhưng không thể chuyển trực tiếp thành khẳng định về mức tiết kiệm thời gian của Second Pair of Eyes vì dự án chưa thực hiện thử nghiệm với reviewer.

PEAR của Proietti et al. (2026) tiếp cận QE theo hướng so sánh cặp: với một câu nguồn và hai bản dịch ứng viên, mô hình dự đoán hướng và mức chênh lệch chất lượng giữa hai bản dịch [11]. Đây là hướng ranking có liên quan, nhưng khác với dự án hiện tại, vốn tạo điểm rủi ro cho từng bản dịch riêng lẻ rồi sắp xếp danh sách. Trong đánh giá, PR curve thường hữu ích khi lớp dương hiếm; Saito và Rehmsmeier (2015) phân tích tính thông tin của PR plot so với ROC plot trên dữ liệu mất cân bằng [14]. Với các chỉ số dựa trên confusion matrix, MCC xem xét đồng thời TP, TN, FP và FN; Chicco và Jurman (2020) trình bày ưu điểm của MCC so với accuracy và F1 trong đánh giá phân loại nhị phân [15].

## 2.5. Khoảng trống và định vị nghiên cứu

Các nghiên cứu gần đây đã phát triển mạnh reference-free QE, phát hiện error span và đánh giá dựa trên neural model hoặc LLM [1], [2], [5]–[11]. Vì vậy, không thể tuyên bố rằng chưa có nghiên cứu về reference-free critical error detection hoặc xếp hạng lỗi dịch. Khoảng trống mà dự án hướng tới hẹp và thực dụng hơn: xây dựng, kiểm toán và đánh giá một baseline học máy cổ điển có thể chạy trên CPU cho nhiệm vụ xếp hạng bản dịch có nguy cơ chứa lỗi nghiêm trọng theo nhãn MQM, trong điều kiện ngân sách rà soát cố định.

Cụ thể, dự án sử dụng Logistic Regression và Linear SVM với TF-IDF cùng các đặc trưng bề mặt; so sánh với Random Ranking và Heuristic Rules; chia dữ liệu theo document; và báo cáo cả PR-AUC lẫn các chỉ số top-20%. Cách định vị này không hàm ý mô hình cổ điển vượt trội so với các hệ thống neural/LLM hiện đại. Mục tiêu là xác định baseline nhẹ có thể đóng góp gì trong một kịch bản ưu tiên rà soát có giới hạn tài nguyên.

# 3. DỮ LIỆU VÀ XÂY DỰNG NHÃN

## 3.1. Nguồn dữ liệu

Nghiên cứu sử dụng tập WMT 2020 MQM English–German thuộc bộ `newstest2020`, với tệp chú giải chính `mqm_newstest2020_ende.tsv`. Kho dữ liệu gốc mô tả đây là dữ liệu MQM cho các đầu ra English-to-German của `newstest2020`; nghiên cứu công bố dữ liệu và repository công khai cung cấp tệp chú giải tương ứng [12], [16]. Repository cũng lưu ý nội dung trong đó không phải là một sản phẩm Google chính thức.

Các trường dữ liệu được sử dụng trong quy trình xử lý gồm:

| Trường          | Ý nghĩa                     |
| --------------- | --------------------------- |
| `system`        | Hệ thống tạo bản dịch       |
| `doc`, `doc_id` | Định danh tài liệu          |
| `seg_id`        | Định danh phân đoạn         |
| `rater`         | Người gán nhãn              |
| `source`        | Câu nguồn tiếng Anh         |
| `target`        | Câu dịch tiếng Đức          |
| `category`      | Danh mục lỗi MQM            |
| `severity`      | Mức độ nghiêm trọng của lỗi |

Kho dữ liệu công khai mô tả tệp `mqm_newstest2020_ende.tsv` là chú giải cho 10 submissions của WMT 2020 English–German. Trong đó có 7 hệ thống dịch máy và 3 đầu ra dịch của con người; ba đầu ra của con người không thuộc phạm vi so sánh bảy hệ thống MT trong tập mô hình của dự án. Sau bước lọc/tổng hợp ở cấp system–document–segment, dữ liệu thực nghiệm của nhóm gồm 9.926 mẫu, 130 tài liệu và 7 hệ thống MT. Cần phân biệt số lượng này với số dòng chú giải MQM ban đầu: một mẫu đánh giá ở cấp phân đoạn có thể liên kết với nhiều dòng chú giải do nhiều người gán nhãn và/hoặc nhiều lỗi được ghi nhận [12], [16].

## 3.2. Định nghĩa nhãn Critical theo quy tắc vận hành

Dự án xây dựng nhãn nhị phân `y_primary` từ chú giải MQM. Một annotation được xem là _serious_ nếu thỏa mãn ít nhất một trong hai điều kiện:

1. `severity == "Major"` và `category` bắt đầu bằng `Accuracy/`; hoặc
2. `category` bằng chính xác `Non-translation!`.

Các annotation được tổng hợp theo từng rater thành một phiếu nhị phân. Sau đó, một phân đoạn được gán `y_primary = 1` nếu ít nhất hai người gán nhãn xác nhận serious error. Có thể biểu diễn quy tắc như sau:

\[
y\_{\text{primary}} =
\begin{cases}
1, & \text{nếu số rater có serious error} \geq 2,\\
0, & \text{ngược lại.}
\end{cases}
\]

Đây là **định nghĩa vận hành của dự án**, không phải định nghĩa phổ quát cho mọi nghiên cứu về lỗi dịch nghiêm trọng. Quy tắc này có hai hệ quả quan trọng. Thứ nhất, severity `Major` tự nó chưa đủ để tạo nhãn dương nếu category không thuộc nhóm được quy định. Thứ hai, nhãn 0 chỉ có nghĩa là phân đoạn không đạt điều kiện positive theo quy tắc này; nó không chứng minh rằng phân đoạn hoàn toàn không có lỗi dịch.

Theo cách tổng hợp này, dữ liệu có 1.183 mẫu Critical và 8.743 mẫu Non-critical. Tỷ lệ lớp dương là:

\[
\frac{1183}{9926} \times 100\% \approx 11.92\%.
\]

Sự mất cân bằng lớp được xem là đặc điểm quan trọng của bài toán và được phản ánh trong lựa chọn metric cũng như cách huấn luyện.

## 3.3. Kiểm soát rò rỉ thông tin

Đầu vào mô hình được giới hạn ở văn bản nguồn, bản dịch máy gốc và các đặc trưng được tính từ hai văn bản này. Các thông tin sau không được sử dụng làm feature dự đoán: `doc_id`, `seg_id`, nhãn MQM, category, severity và thông tin người gán nhãn. Marker chú giải như `<v>...</v>` cần được loại bỏ khỏi văn bản đầu vào để mô hình không tiếp cận trực tiếp vị trí lỗi được người đánh giá đánh dấu.

Một yêu cầu quan trọng khác là đặc trưng phải được trích xuất từ đầu ra MT gốc, không phải từ bản dịch đã được chèn marker chú giải. Nếu sử dụng bản đã chú giải, mô hình có thể khai thác dấu vết của quy trình đánh giá, làm sai lệch bản chất reference-free.

## 3.4. Chia tập dữ liệu theo tài liệu

Dữ liệu được chia theo tài liệu thay vì chia ngẫu nhiên từng phân đoạn. Lý do là các phân đoạn trong cùng tài liệu có thể chia sẻ chủ đề, thuật ngữ, phong cách và ngữ cảnh. Nếu các phân đoạn của cùng một tài liệu xuất hiện đồng thời trong Train và Test, mô hình có thể hưởng lợi từ sự tương đồng ngữ cảnh, khiến kết quả đánh giá lạc quan hơn.

| Tập      | Số tài liệu |    Số mẫu | Số mẫu Critical |
| -------- | ----------: | --------: | --------------: |
| Train    |          90 |     6.797 |             803 |
| Dev      |          20 |     1.554 |             218 |
| Test     |          20 |     1.575 |             162 |
| **Tổng** |     **130** | **9.926** |       **1.183** |

Tỷ lệ Critical theo từng tập lần lượt xấp xỉ 11,81% ở Train, 14,03% ở Dev và 10,29% ở Test. Tài liệu G4.3.5 ghi nhận việc sử dụng `GroupShuffleSplit` với các seed 42 và 43 để tạo các phân vùng theo document. Trước khi khóa bản nộp, cần đối chiếu script chia dữ liệu để mô tả chính xác thứ tự hai lần chia và tham số của từng lần; bảng số lượng và snapshot Week 10 hiện là căn cứ báo cáo chính.

Các kiểm tra QA được ghi nhận gồm: không có tài liệu trùng giữa các tập, không có khóa trùng `system/doc/seg_id` và không có giá trị bắt buộc bị thiếu trong dữ liệu phân đoạn đã kiểm tra. Các artefact split được lưu tại `results/week10/locked_split/`. Hash SHA-256 được ghi trong manifest là `780cd9f0b2b32042ad95f98e67318c03814fbe895e1f0ef8755da847e8d287ab`.

Trạng thái split được ghi là `candidate_locked`. Việc xác minh hiện có cho thấy tính nhất quán giữa snapshot, hash và phân công tài liệu; tuy nhiên, nó không tự chứng minh rằng split đã được tái tạo độc lập từ dữ liệu thô, cũng không chứng minh Test chưa từng được xem trong các giai đoạn phát triển trước đó. Do đó, báo cáo không đưa ra tuyên bố mạnh hơn bằng chứng hiện có.

## 3.5. Tiền xử lý và xử lý mất cân bằng

Các thành phần học được từ dữ liệu như TF-IDF vectorizer và bộ chuẩn hóa đặc trưng được fit chỉ trên Train; Dev được dùng để so sánh cấu hình. Test được dành cho đánh giá cuối theo quy trình được mô tả trong README. Cách tổ chức này nhằm tránh việc thông tin thống kê từ Dev hoặc Test ảnh hưởng ngược trở lại quá trình học biểu diễn trên Train.

Hai mô hình Logistic Regression và Linear SVM sử dụng `class_weight="balanced"` để điều chỉnh trọng số lớp theo phân bố dữ liệu. Báo cáo không mô tả việc sử dụng SMOTE hoặc oversampling vì quy trình hiện được ghi nhận không cho thấy các kỹ thuật đó được áp dụng.

---

# 4. PHƯƠNG PHÁP VÀ THIẾT KẾ THỰC NGHIỆM

## 4.1. Quy trình tổng thể

Pipeline của Second Pair of Eyes có thể mô tả qua các bước:

1. Nhận cặp văn bản nguồn tiếng Anh và đầu ra MT tiếng Đức.
2. Tiền xử lý văn bản và loại bỏ marker chú giải nếu có.
3. Trích xuất biểu diễn TF-IDF từ văn bản nguồn và bản dịch, kết hợp với 12 đặc trưng bề mặt.
4. Đưa vector đặc trưng vào mô hình đã huấn luyện.
5. Tạo điểm số rủi ro cho từng phân đoạn.
6. Sắp xếp phân đoạn theo điểm rủi ro giảm dần.
7. Chuyển top 20% thành hàng đợi ưu tiên để người rà soát kiểm tra.

Pipeline không cần bản dịch tham chiếu ở bước dự đoán. Nhãn MQM chỉ được sử dụng trong huấn luyện và đánh giá ngoại tuyến.

## 4.2. Biểu diễn đặc trưng

Hai mô hình học máy sử dụng hai nhóm đặc trưng: biểu diễn TF-IDF riêng cho văn bản nguồn và văn bản đích, kết hợp 12 đặc trưng bề mặt được tính trực tiếp từ cặp văn bản.

**TF-IDF.** Văn bản nguồn tiếng Anh và bản dịch tiếng Đức được đưa qua hai vectorizer riêng. Cấu hình được ghi nhận trong tài liệu kiểm toán phương pháp gồm word n-gram với `ngram_range=(1, 2)`, `max_features=30.000` cho mỗi vectorizer, `min_df=2` và `sublinear_tf=True`. Hai vectorizer riêng cho phép mô hình học tín hiệu từ vựng ở cả nguồn và đích mà không cần bản dịch tham chiếu.

**Mười hai đặc trưng bề mặt.**

| STT | Đặc trưng                            | Ý nghĩa                                    |
| --: | ------------------------------------ | ------------------------------------------ |
|   1 | Log source token count               | Số token nguồn sau biến đổi log            |
|   2 | Log target token count               | Số token đích sau biến đổi log             |
|   3 | Target/source token ratio            | Tỷ lệ số token đích trên nguồn             |
|   4 | Relative token-count difference      | Chênh lệch số token tương đối so với nguồn |
|   5 | Target/source character-length ratio | Tỷ lệ độ dài ký tự giữa đích và nguồn      |
|   6 | Source digit count                   | Số chữ số trong văn bản nguồn              |
|   7 | Target digit count                   | Số chữ số trong bản dịch                   |
|   8 | Absolute digit-count difference      | Chênh lệch tuyệt đối số chữ số             |
|   9 | Target uppercase ratio               | Tỷ lệ ký tự viết hoa trong bản dịch        |
|  10 | Target punctuation/symbol ratio      | Tỷ lệ dấu câu và ký hiệu trong bản dịch    |
|  11 | Repeated-token count                 | Số lượng token lặp lại trong bản dịch      |
|  12 | Empty-target indicator               | Biến chỉ báo bản dịch rỗng                 |

Các đặc trưng này phản ánh một số dấu hiệu bề mặt có thể liên quan đến chất lượng bản dịch, chẳng hạn độ dài bất thường, sai lệch chữ số, lặp token hoặc bản dịch rỗng. Chúng không trực tiếp xác định một lỗi ngữ nghĩa là nghiêm trọng hay không. Đặc tả trên được lấy từ bản G4.3.4; trước khi nộp, cần đối chiếu tên, thứ tự và công thức tính từng feature với mã nguồn triển khai để bảo đảm không có sai khác giữa tài liệu và code.

## 4.3. Các mô hình và baseline

Bốn phương pháp được so sánh:

- **Random ranking:** xếp hạng ngẫu nhiên, đóng vai trò mốc tham chiếu tối thiểu.
- **Heuristic Rules:** gán điểm ưu tiên dựa trên một số bất thường bề mặt được xác định trước.
- **Logistic Regression:** mô hình tuyến tính kết hợp TF-IDF và 12 đặc trưng bề mặt.
- **Linear SVM:** mô hình phân tách tuyến tính sử dụng cùng biểu diễn đặc trưng tổng quát với Logistic Regression.

Cấu hình mô hình được ghi trong bản G4.3.4 như sau:

| Mô hình             | Tham số        |    Giá trị |
| ------------------- | -------------- | ---------: |
| Logistic Regression | `C`            |          1 |
| Logistic Regression | `max_iter`     |      2.000 |
| Logistic Regression | `random_state` |         42 |
| Logistic Regression | `class_weight` | `balanced` |
| Linear SVM          | `C`            |          1 |
| Linear SVM          | `max_iter`     |     10.000 |
| Linear SVM          | `class_weight` | `balanced` |

Logistic Regression tạo xác suất dự đoán lớp Critical và xác suất này được dùng để xếp hạng. Linear SVM sử dụng decision score để xếp hạng; điểm này không được diễn giải là xác suất đã hiệu chỉnh nếu không có bước calibration. Cần kiểm tra lại tên lớp triển khai cụ thể trong mã nguồn (ví dụ `LinearSVC`) trước khi ghi tên API scikit-learn trong bản nộp.

Random baseline trên Dev là trung bình của 100 lần xếp hạng ngẫu nhiên với seed từ 42 đến 141, đồng thời báo cáo độ lệch chuẩn mẫu. Ngược lại, Random baseline trên Test sử dụng một lần xếp hạng với seed `20261026`. Sự khác nhau này phải được giữ rõ khi diễn giải: hai kết quả Random Dev và Test không phải ước lượng được tạo ra từ cùng một quy trình lặp.

## 4.4. Ablation study trên Dev

Nhóm đánh giá ba cấu hình Logistic Regression:

- `LR_Base`: cấu hình cơ sở.
- `LR_Plus_System`: bổ sung danh tính hệ thống MT.
- `System_Only`: chỉ sử dụng thông tin hệ thống MT.

Mục tiêu là xem danh tính hệ thống có bổ sung thông tin hữu ích cho việc xếp hạng hay không, và liệu tín hiệu này có cải thiện kết quả ở ngân sách rà soát cố định hay không. Ablation được thực hiện trên Dev; các con số được diễn giải như point estimates, không phải kiểm định ý nghĩa thống kê.

## 4.5. Thiết lập ngân sách rà soát

Ngân sách vận hành chính là 20% số phân đoạn trong tập đánh giá. Với mỗi tập, mô hình xếp hạng toàn bộ mẫu theo điểm rủi ro và chọn phần đầu danh sách có kích thước bằng 20% tổng số mẫu (theo số nguyên được sử dụng trong artefact đánh giá). Trên Dev, ngân sách là 311/1.554 mẫu; trên Test, ngân sách là 315/1.575 mẫu.

Thiết lập này mô phỏng tình huống người rà soát không thể kiểm tra mọi bản dịch và cần chọn một tập con để ưu tiên. Do đó, các chỉ số @20% có ý nghĩa trực tiếp đối với mục tiêu triển khai hơn là chỉ xem xét một ngưỡng phân loại độc lập với khối lượng công việc.

## 4.6. Ước lượng độ bất định

Độ bất định trên Test được ước lượng bằng 1.000 lần paired document-cluster bootstrap, seed `20261027`. Đơn vị lấy mẫu là tài liệu: khi một tài liệu được lấy mẫu, các phân đoạn thuộc tài liệu đó được giữ cùng nhau. Khi so sánh hai mô hình, cùng một tập tài liệu bootstrap được sử dụng cho cả hai mô hình để tạo chênh lệch theo cặp.

Cách làm này tôn trọng cấu trúc cụm của dữ liệu tốt hơn việc coi mọi phân đoạn là quan sát độc lập. Tuy nhiên, Test chỉ gồm 20 tài liệu, nên các khoảng tin cậy vẫn cần được diễn giải thận trọng. Bootstrap không loại bỏ được các giới hạn do định nghĩa nhãn, bất đồng annotator hoặc lịch sử tiếp xúc với Test.

---

# 5. KẾT QUẢ THỰC NGHIỆM

## 5.1. Kết quả so sánh các phương pháp trên Dev

Tập Dev gồm 1.554 mẫu, trong đó có 218 mẫu Critical, tương ứng tỷ lệ dương tính khoảng 14,03%. Ngân sách rà soát 20% là 311 mẫu. Bảng dưới đây tích hợp kết quả baseline Dev được trình bày trong tài liệu G4.3.6.

| Phương pháp         |     PR-AUC | Precision@20% | Recall@20% | Lift@20% |    MCC@20% |
| ------------------- | ---------: | ------------: | ---------: | -------: | ---------: |
| Random              |     0,1435 |        0,1399 |     0,1996 |     1,00 |    -0,0005 |
| Heuristic Rules     |     0,1777 |    **0,2315** | **0,3303** | **1,65** | **0,1314** |
| Logistic Regression | **0,1961** |        0,2026 |     0,2890 |     1,44 |     0,0897 |
| Linear SVM          |     0,1742 |        0,1929 |     0,2752 |     1,38 |     0,0758 |

Trên Dev, Logistic Regression có PR-AUC cao nhất, nhưng Heuristic Rules đạt kết quả cao hơn ở cả bốn chỉ số vận hành tại top 20%. Đây là một khác biệt quan trọng: chất lượng xếp hạng tổng thể trên nhiều ngưỡng không đồng nhất với hiệu quả trong một danh sách có kích thước cố định. Heuristic vì vậy là baseline cạnh tranh, không phải mốc yếu chỉ để mô hình học máy vượt qua.

Linear SVM có point estimates thấp hơn Logistic Regression ở cả năm chỉ số trong bảng. Tuy nhiên, không có khoảng tin cậy hoặc kiểm định thống kê riêng cho bảng so sánh Dev này; các chênh lệch nên được mô tả như kết quả quan sát trên tập Dev.

## 5.2. Kết quả ablation trên Dev

| Cấu hình       | PR-AUC | Precision@20% | Recall@20% | Lift@20% | MCC@20% |
| -------------- | -----: | ------------: | ---------: | -------: | ------: |
| LR_Base        | 0,1961 |        0,2026 |     0,2890 |   1,4440 |  0,0897 |
| LR_Plus_System | 0,1991 |        0,1961 |     0,2798 |   1,3982 |  0,0805 |
| System_Only    | 0,1568 |        0,1768 |     0,2523 |   1,2607 |  0,0527 |

`LR_Plus_System` có PR-AUC cao hơn `LR_Base` một lượng nhỏ (0,1991 so với 0,1961). Tuy nhiên, khi xét đúng mục tiêu ưu tiên rà soát trong top 20%, cấu hình bổ sung system identity lại có Precision, Recall, Lift và MCC thấp hơn cấu hình cơ sở. `System_Only` có kết quả thấp hơn `LR_Base` ở tất cả các chỉ số được báo cáo.

Vì mục tiêu chính của dự án là tối ưu thứ tự ưu tiên dưới ngân sách kiểm tra hữu hạn, nhóm giữ `LR_Base` làm cấu hình chính. Quyết định này dựa trên các point estimates của Dev và định hướng vận hành đã xác định. Do không có khoảng tin cậy hoặc kiểm định ý nghĩa thống kê cho ablation, không nên diễn giải chênh lệch này như bằng chứng về khác biệt có ý nghĩa thống kê.

## 5.3. Kết quả trên Test

Tập Test gồm 1.575 mẫu thuộc 20 tài liệu, trong đó có 162 mẫu Critical. Tỷ lệ lớp dương là 10,29%. Với ngân sách 20%, hệ thống chọn 315 mẫu để rà soát.

| Phương pháp         |     PR-AUC | Precision@20% | Recall@20% |   Lift@20% |    MCC@20% |
| ------------------- | ---------: | ------------: | ---------: | ---------: | ---------: |
| Random              |     0,1091 |        0,1016 |     0,1975 |     0,9877 |    -0,0021 |
| Heuristic Rules     |     0,1391 |        0,1587 |     0,3086 |     1,5432 |     0,0920 |
| Logistic Regression | **0,1971** |    **0,1619** | **0,3148** | **1,5741** | **0,0972** |
| Linear SVM          |     0,1676 |        0,1206 |     0,2346 |     1,1728 |     0,0293 |

Logistic Regression đạt PR-AUC cao nhất (0,1971), tiếp theo là Linear SVM (0,1676), Heuristic Rules (0,1391) và Random (0,1091). Kết quả này cho thấy Logistic Regression có khả năng phân biệt và sắp xếp mẫu theo mức độ rủi ro tốt hơn trên toàn bộ dải ngưỡng của tập Test theo chỉ số PR-AUC.

Tuy nhiên, chênh lệch ở ngân sách 20% nhỏ hơn đáng kể. Trong 315 mẫu được chọn, Logistic Regression phát hiện 51 mẫu Critical, còn Heuristic Rules phát hiện 50 mẫu. Precision@20% lần lượt là 0,1619 và 0,1587; Recall@20% lần lượt là 0,3148 và 0,3086. Nói cách khác, dù Logistic Regression đứng đầu ở các point estimates, lợi ích thực tế so với heuristic trong top 20% chỉ tương đương một mẫu Critical bổ sung.

## 5.4. So sánh theo paired bootstrap

Chênh lệch PR-AUC giữa Logistic Regression và Heuristic Rules là:

\[
\Delta \text{PR-AUC} = 0.1971 - 0.1391 = 0.0580.
\]

Khoảng tin cậy paired document-cluster bootstrap 95% được báo cáo là:

\[
[0.0151,\ 0.1232].
\]

Khoảng này không chứa 0, do đó kết quả hỗ trợ nhận định rằng PR-AUC của Logistic Regression cao hơn Heuristic Rules trong phép đánh giá Test hiện tại theo quy trình bootstrap đã sử dụng.

Tuy nhiên, các khoảng tin cậy của chênh lệch ở các chỉ số vận hành cố định tại top 20% — Precision, Recall, Lift và MCC — đều bao gồm 0. Vì vậy, bằng chứng thống kê hiện tại **không đủ để khẳng định Logistic Regression có ưu thế vận hành rõ ràng tại ngân sách rà soát 20%**. Cần tách biệt hai kết luận: (i) mô hình có PR-AUC tốt hơn trên toàn bộ thứ hạng; và (ii) mức cải thiện trong phần danh sách mà reviewer thực sự kiểm tra còn rất nhỏ và chưa được xác nhận rõ qua khoảng tin cậy.

## 5.5. Trả lời sơ bộ các câu hỏi nghiên cứu

- **RQ1:** Nhóm xây dựng nhãn Critical bằng cách kết hợp category, severity và quy tắc đồng thuận ít nhất 2/3 annotators. Đây là định nghĩa vận hành có phạm vi cụ thể, không phải ground truth phổ quát.
- **RQ2:** Logistic Regression đạt PR-AUC cao nhất trên Test so với Random, Heuristic Rules và Linear SVM. Tuy nhiên, ưu thế ở top 20% là nhỏ; chưa có bằng chứng đủ mạnh để kết luận ưu thế vận hành rõ ràng so với heuristic.
- **RQ3:** Trên Dev, bổ sung system identity làm PR-AUC tăng nhẹ nhưng làm giảm các chỉ số top-20%; cấu hình `LR_Base` được giữ lại. Kết quả này không chứng minh khả năng tổng quát hóa sang hệ thống MT chưa xuất hiện trong dữ liệu.
- **RQ4:** Kiểm toán Dev cho thấy các trường hợp được xếp hạng cao nhưng không đạt nhãn Critical có thể vẫn có lỗi MQM không nghiêm trọng, bất đồng annotator hoặc vấn đề khớp annotation. Phân tích định tính cung cấp ví dụ minh họa nhưng chưa đủ để khái quát cho mọi loại lỗi.

---

# 6. PHÂN TÍCH LỖI VÀ KIỂM TOÁN MQM

## 6.1. Mục đích phân tích

Chỉ số tổng hợp cho biết mô hình xếp hạng tốt đến đâu, nhưng không giải thích đầy đủ vì sao một số phân đoạn được đưa lên đầu danh sách mà không đạt nhãn Critical. Với hệ thống hỗ trợ rà soát, những trường hợp này cần được phân tích cẩn thận. Chúng có thể là false positives theo nhãn vận hành, nhưng cũng có thể là trường hợp chứa lỗi không nghiêm trọng, bất đồng giữa người đánh giá hoặc thiếu sót trong quá trình đối chiếu annotation.

Vì vậy, báo cáo sử dụng cách gọi **high-ranked non-critical cases** hoặc **zero-vote cases**, thay vì mặc định gọi tất cả là false positives. Cách gọi này tránh giả định rằng nhãn 0 đồng nghĩa với bản dịch hoàn toàn đúng.

## 6.2. Kiểm toán 180 phân đoạn zero-vote trên Dev

Phân tích bắt đầu từ 311 mẫu nằm trong top 20% dự đoán bởi `LR_Base` trên Dev. Trong số đó, 180 mẫu có `serious_votes = 0` và `y_primary = 0`.

Để đối chiếu chú giải, nhóm sử dụng quy trình chuẩn hóa target gồm loại bỏ marker `<v>`, chuẩn hóa Unicode NFKC và gộp khoảng trắng. Có 959 dòng annotation ứng viên được truy xuất; 893 dòng khớp target sau chuẩn hóa và 66 dòng không khớp. Không có segment key nào trong 180 mẫu bị mất hoàn toàn annotation khớp.

Phân bố trạng thái MQM sau đối chiếu nghiêm ngặt:

| Trạng thái MQM           | Số phân đoạn |       Tỷ lệ |
| ------------------------ | -----------: | ----------: |
| Chỉ có lỗi Minor         |          149 |      82,78% |
| Không ghi nhận lỗi MQM   |           30 |      16,67% |
| Có cả lỗi Minor và Major |            1 |       0,56% |
| **Tổng**                 |      **180** | **100,00%** |

Như vậy, 150/180 phân đoạn (83,33%) có ít nhất một annotation MQM không thuộc nhãn Critical sau khi khớp target. Kết quả này cho thấy nhiều trường hợp không đạt nhãn Critical vẫn có thể mang vấn đề chất lượng dịch ở mức khác. Điều đó phù hợp với bản chất của nhãn nhị phân đã được xây dựng: nhãn 0 chỉ cho biết không đủ phiếu serious theo tiêu chí dự án, không khẳng định không có bất kỳ lỗi nào.

Kiểm toán cũng ghi nhận bất đồng giữa người gán nhãn ở 77/180 phân đoạn (42,78%). Độ bao phủ rater không đồng đều: 163 phân đoạn có ba rater, 14 phân đoạn có hai rater và 3 phân đoạn có một rater. Vì vậy, 30 trường hợp “No MQM Error Recorded” không được mô tả là các trường hợp cả ba rater nhất trí rằng không có lỗi. Đây là khác biệt quan trọng giữa “không ghi nhận lỗi trong annotation khớp” và “được ba người đánh giá xác nhận không có lỗi”.

Có 66 dòng annotation không khớp target, chiếm 6,88% số dòng ứng viên. Đây là số dòng ở cấp annotation, không phải 66 phân đoạn không thể đối chiếu. Tất cả 180 segment key đều có ít nhất một annotation khớp. Do đó, không được diễn giải 66 dòng này thành 66 mẫu bị mất nhãn.

## 6.3. Kiểm toán định tính 10 trường hợp

Nhóm tiếp tục kiểm tra sâu 10 trường hợp Dev có thứ hạng cao nhưng `y_primary = 0`. Đây là mẫu chọn có chủ đích, không phải mẫu ngẫu nhiên. Kết quả đối chiếu gồm 47 dòng annotation ứng viên, 42 dòng khớp và 5 dòng không khớp. Cả 10 trường hợp đều có ít nhất một annotation khớp và đều có số phiếu serious được tính lại bằng 0.

Mười trường hợp tương ứng với năm source segment duy nhất thuộc bốn tài liệu. Sáu trường hợp (Cases 3, 4, 6, 7, 8 và 9) là các hệ thống MT khác nhau dịch cùng một source segment. Vì vậy, chúng không phải sáu quan sát độc lập ở cấp nội dung nguồn. Đặc điểm này giới hạn mức độ khái quát của phân tích định tính.

Hai trường hợp cho thấy vì sao cần kết hợp category, severity và kiểm tra target matching:

**Trường hợp Online-B, abcnews, document 5, segment 1317.** Có 11 dòng annotation ứng viên, trong đó 6 dòng khớp target và 5 dòng không khớp. Một annotation Major xuất hiện trong nhóm không khớp; các annotation khớp là Minor. Do đó, annotation Major không khớp không được dùng làm bằng chứng rằng bản dịch được chọn có lỗi Critical.

**Trường hợp eTranslation, standard.co.uk, document 1, segment 1386.** Cả ba dòng annotation ứng viên đều khớp. Tuy nhiên, annotation Major thuộc category `Style/Awkward`, nằm ngoài định nghĩa Critical vận hành của dự án. Trường hợp này minh họa rằng severity Major không tự động đồng nghĩa với nhãn dương.

Nhìn chung, các trường hợp được xem xét cho thấy điểm rủi ro cao có thể xuất hiện ở các bản dịch có lỗi MQM không nghiêm trọng, có vấn đề bất đồng hoặc có sự khác biệt trong đối chiếu annotation. Mô hình vì thế nên được hiểu là bộ xếp hạng tín hiệu để con người xem xét, không phải bộ phân xử cuối cùng.

## 6.4. Giới hạn của phân tích lỗi

Phân tích 10 trường hợp không được chọn ngẫu nhiên, chỉ bao gồm các trường hợp zero-vote và có các source segment lặp lại giữa nhiều hệ thống MT. Các diễn giải được thực hiện bởi nhóm dự án, không phải kết quả thẩm định độc lập của chuyên gia dịch thuật. Không có mẫu positive-label trong tập 10 trường hợp. Do đó, phân tích này không cho phép kết luận về cách mô hình xử lý toàn bộ các loại lỗi hoặc các trường hợp Critical thực sự.

Các kết quả 180 mẫu và 10 trường hợp được dùng để giải thích sự phức tạp của nhãn và hành vi xếp hạng, không được dùng để khẳng định rằng mô hình thường xuyên dự đoán sai hoặc rằng mọi mẫu zero-vote đều là lỗi của người gán nhãn.

---

# 7. THẢO LUẬN

## 7.1. Ý nghĩa của kết quả định lượng

Kết quả Test cho thấy Logistic Regression là mô hình có PR-AUC cao nhất trong các phương pháp được đánh giá. Điều này cho thấy mô hình có khả năng sắp xếp các mẫu Critical lên phía trên danh sách tốt hơn các phương pháp còn lại trên toàn bộ các ngưỡng. Tuy nhiên, khi chuyển sang kịch bản vận hành cụ thể — chỉ rà soát 20% số phân đoạn — khoảng cách với heuristic thu hẹp đáng kể: 51 so với 50 mẫu Critical được tìm thấy.

Sự khác biệt này có ý nghĩa đối với cách đánh giá một hệ thống ưu tiên rà soát. Một mô hình có thể cải thiện chất lượng xếp hạng tổng thể nhưng không tạo ra mức tăng tương ứng trong phần đầu danh sách mà con người có thể kiểm tra. Vì vậy, chỉ báo cáo PR-AUC sẽ chưa đủ để kết luận hệ thống mang lại lợi ích vận hành rõ ràng. Cần xem đồng thời các chỉ số tại ngân sách cố định và độ bất định của chênh lệch.

## 7.2. So sánh học máy với heuristic

Heuristic Rules đạt kết quả tốt hơn Random ở các chỉ số top-20%, cho thấy các bất thường bề mặt đơn giản có thể cung cấp tín hiệu hữu ích cho việc ưu tiên rà soát. Logistic Regression cải thiện PR-AUC so với heuristic, nhưng chỉ tăng một mẫu Critical trong top 315. Kết quả này gợi ý rằng mô hình học máy có thể khai thác thêm thông tin từ biểu diễn văn bản, song giá trị gia tăng trong điều kiện ngân sách cố định hiện chưa lớn.

Không nên xem heuristic là một baseline yếu hoặc không có giá trị. Trong một hệ thống thực tế, heuristic có ưu điểm dễ kiểm tra, dễ giải thích và chi phí tính toán thấp. Mô hình học máy chỉ nên được ưu tiên nếu lợi ích bổ sung được xác nhận ổn định trên dữ liệu mới và trong đúng kịch bản sử dụng.

## 7.3. Vai trò của system identity

Ablation trên Dev cho thấy thêm danh tính hệ thống làm PR-AUC tăng nhẹ nhưng giảm Precision@20%, Recall@20%, Lift@20% và MCC@20%. System-only cũng thấp hơn cấu hình cơ sở. Điều này cho thấy danh tính hệ thống có thể chứa thông tin tương quan với nhãn, nhưng không nhất thiết cải thiện khả năng chọn đúng các mẫu Critical ở phần đầu danh sách.

Một khả năng cần kiểm tra trong nghiên cứu tiếp theo là liệu system identity giúp mô hình học đặc điểm của các hệ thống đã xuất hiện trong tập dữ liệu thay vì học tín hiệu có thể chuyển giao sang hệ thống mới hay không. Tuy nhiên, kết quả hiện tại chưa phải đánh giá trên unseen MT systems, nên đây chỉ là hướng giải thích và giả thuyết cần kiểm chứng thêm.

## 7.4. Hàm ý đối với quy trình human review

Second Pair of Eyes phù hợp hơn với vai trò một bộ lọc ưu tiên hơn là bộ phân loại tự động để chấp nhận hoặc từ chối bản dịch. Một quy trình triển khai hợp lý có thể sử dụng điểm rủi ro để sắp xếp danh sách, sau đó reviewer kiểm tra các trường hợp đầu danh sách và đưa ra quyết định dựa trên ngữ cảnh đầy đủ.

Phân tích 180 mẫu zero-vote cho thấy nhiều mẫu vẫn có annotation Minor hoặc bất đồng giữa người gán nhãn. Điều này cho thấy “false positive” trong đánh giá nhị phân có thể bao gồm những trường hợp vẫn đáng để con người kiểm tra, dù chúng không thỏa định nghĩa Critical. Tuy nhiên, không thể từ đó suy ra rằng mọi mẫu được xếp hạng cao đều hữu ích hoặc việc rà soát chúng chắc chắn tiết kiệm thời gian. Muốn chứng minh lợi ích thực tế, cần có nghiên cứu người dùng hoặc thử nghiệm quy trình với reviewer, đo thời gian rà soát và số lỗi quan trọng được phát hiện.

---

# 8. HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN

## 8.1. Hạn chế

**Định nghĩa nhãn.** Nhãn Critical được xây dựng theo quy tắc cụ thể về category, severity và đồng thuận annotator. Đây không phải ground truth phổ quát. Các trường hợp không đạt nhãn dương vẫn có thể chứa lỗi Minor hoặc vấn đề chất lượng khác.

**Bất đồng và độ bao phủ annotator.** Phân tích Dev cho thấy có bất đồng giữa người gán nhãn và số lượng rater không đồng đều ở một số mẫu. Điều này làm tăng bất định khi diễn giải nhãn 0.

**Mất cân bằng lớp.** Lớp Critical chiếm khoảng 11,92% dữ liệu tổng hợp. Dù mô hình sử dụng balanced class weights và báo cáo các metric hướng đến lớp dương, mất cân bằng vẫn ảnh hưởng đến việc học và đánh giá.

**Quy mô Test.** Test gồm 20 tài liệu. Bootstrap theo cụm tài liệu phù hợp hơn việc coi các phân đoạn độc lập, nhưng số cụm còn hạn chế nên khoảng tin cậy cần được diễn giải thận trọng.

**Ưu thế vận hành chưa rõ ràng.** Logistic Regression có PR-AUC cao nhất, nhưng chỉ phát hiện thêm một mẫu Critical so với heuristic trong top 20%; các khoảng tin cậy của chênh lệch chỉ số vận hành đều bao gồm 0.

**Ablation và khả năng tổng quát hóa.** Ablation system identity chỉ được báo cáo bằng point estimates trên Dev. Chưa có bằng chứng về ý nghĩa thống kê hoặc khả năng tổng quát hóa sang các hệ thống MT chưa xuất hiện.

**Quy trình random baseline khác nhau.** Random trên Dev là trung bình 100 lần xếp hạng, trong khi Random trên Test là một lần xếp hạng với seed cố định. Hai kết quả không thể được xem là hoàn toàn tương đương về quy trình.

**Lịch sử tiếp xúc với Test.** Split hiện ở trạng thái `candidate_locked`. Kiểm tra xác nhận tính nhất quán của artefact, hash và phân công tài liệu, nhưng không chứng minh Test chưa từng được xem trong giai đoạn phát triển trước đó.

**Phạm vi dữ liệu.** Thực nghiệm giới hạn ở WMT 2020 English–German và bảy hệ thống MT. Chưa chứng minh khả năng chuyển giao sang cặp ngôn ngữ, miền dữ liệu hoặc hệ thống MT khác.

**Phân tích định tính.** Mẫu 10 trường hợp không ngẫu nhiên, chỉ gồm zero-vote và có source segment lặp lại. Nhận định do nhóm thực hiện, không phải expert adjudication.

**Tái lập.** Các kiểm tra tái lập được thực hiện trong sandbox riêng trên cùng một máy, chưa phải tái lập độc lập trên máy tính hoặc hệ điều hành khác.

**Giấy phép dữ liệu.** Cần kiểm tra điều khoản của từng thành phần dữ liệu. Không được suy luận rằng giấy phép Apache 2.0 ở cấp repository tự động cho phép phân phối lại mọi dữ liệu thành phần hoặc đầu ra MT của bên thứ ba.

## 8.2. Hướng phát triển

Các hướng tiếp theo nên ưu tiên giải quyết trực tiếp những giới hạn trên:

1. **Kiểm định trên dữ liệu ngoài mẫu:** đánh giá trên tập dữ liệu khác, cặp ngôn ngữ khác hoặc hệ thống MT chưa xuất hiện để kiểm tra khả năng tổng quát hóa.
2. **Mở rộng đánh giá theo ngân sách:** báo cáo thêm các mức ngân sách khác nhau (ví dụ 5%, 10%, 20%, 30%) để xem mô hình có hữu ích trong các kịch bản nhân lực khác nhau hay không.
3. **Phân tích độ nhạy của nhãn:** so sánh các quy tắc đồng thuận khác nhau nếu được thiết kế và báo cáo rõ ràng; không thay đổi định nghĩa nhãn sau khi xem Test mà không có một tập đánh giá độc lập.
4. **Kiểm tra hiệu chỉnh điểm số:** nếu hệ thống được dùng để diễn giải điểm rủi ro như xác suất, cần đánh giá calibration riêng; không mặc định decision score của Linear SVM là xác suất.
5. **Thử nghiệm với reviewer:** đo thời gian rà soát, số Critical được phát hiện, số trường hợp không cần thiết phải kiểm tra và mức độ đồng thuận giữa reviewer.
6. **Kiểm toán đặc trưng:** công bố đầy đủ định nghĩa và công thức của 12 surface features, cùng kiểm tra ablation từng nhóm đặc trưng.
7. **Tăng cường tái lập:** thực hiện chạy lại từ dữ liệu gốc trong môi trường độc lập, lưu phiên bản thư viện, cấu hình, seed, hash và log đầy đủ.
8. **Hoàn thiện provenance và license:** xác minh quyền sử dụng, quyền phân phối lại của dữ liệu chú giải, mapping và original MT outputs trước khi công bố artefact.

---

# 9. KẾT LUẬN

Báo cáo đã trình bày quá trình xây dựng và đánh giá Second Pair of Eyes, một hệ thống hỗ trợ xếp hạng rủi ro lỗi dịch máy nghiêm trọng theo hướng reference-free trên dữ liệu WMT 2020 MQM English–German. Nhóm xây dựng nhãn Critical từ category, severity và quy tắc đồng thuận ít nhất hai annotator; thiết kế chia tập theo tài liệu; so sánh Logistic Regression và Linear SVM với random ranking và heuristic rules; đồng thời phân tích các trường hợp Dev được xếp hạng cao nhưng không đạt nhãn Critical.

Kết quả Test cho thấy Logistic Regression đạt PR-AUC 0,1971, cao hơn Heuristic Rules (0,1391), Linear SVM (0,1676) và Random (0,1091). Chênh lệch PR-AUC giữa Logistic Regression và Heuristic Rules có khoảng tin cậy paired bootstrap 95% không chứa 0. Tuy nhiên, trong top 20% số mẫu, Logistic Regression chỉ phát hiện 51 mẫu Critical so với 50 của heuristic; các khoảng tin cậy của chênh lệch chỉ số vận hành tại ngân sách này đều bao gồm 0. Do đó, kết luận phù hợp nhất là Logistic Regression cho thứ hạng tổng thể tốt hơn theo PR-AUC trong phép đánh giá hiện tại, nhưng chưa chứng minh ưu thế vận hành rõ ràng trong kịch bản rà soát 20%.

Phân tích lỗi cho thấy nhãn Non-critical không đồng nghĩa với không có vấn đề chất lượng dịch. Nhiều trường hợp zero-vote vẫn có annotation Minor, và một số trường hợp có bất đồng giữa người gán nhãn. Các ví dụ định tính cũng cho thấy cần xem xét category, severity và target matching đồng thời. Điều này củng cố định hướng human-in-the-loop: mô hình nên hỗ trợ sắp xếp thứ tự ưu tiên, còn quyết định cuối cùng cần được thực hiện bởi người có chuyên môn.

Trong phạm vi dữ liệu và thiết kế hiện tại, Second Pair of Eyes là một baseline học máy cổ điển có khả năng chạy trên CPU và cung cấp tín hiệu xếp hạng hữu ích để nghiên cứu tiếp. Tuy nhiên, để khẳng định giá trị triển khai, cần có đánh giá độc lập trên dữ liệu mới và thử nghiệm trực tiếp với quy trình rà soát của con người.

---

# TÀI LIỆU THAM KHẢO

Danh mục dưới đây ưu tiên các công trình công bố giai đoạn 2023–2026, đặc biệt là các bài năm 2026. Thông tin thư mục được đối chiếu với trang xuất bản chính thức của ACL Anthology, tạp chí hoặc kho dữ liệu công khai. Các bài WMT26/ACL 2026 được công bố toàn văn trên ACL Anthology và có PDF truy cập công khai tại trang bài báo.

[1] Blain, F., Zerva, C., Rei, R., Guerreiro, N. M., Kanojia, D., de Souza, J. G. C., Silva, B., Vaz, T., Jingxuan, Y., Azadi, F., Orăsan, C., & Martins, A. F. T. (2023). Findings of the WMT 2023 Shared Task on Quality Estimation. _Proceedings of the Eighth Conference on Machine Translation_, 629–653. Association for Computational Linguistics. https://doi.org/10.18653/v1/2023.wmt-1.52

[2] Lavie, A., Hanneman, G., Perrella, S., Ding, S., Avramidis, E., Proietti, L., Lo, C.-K., Shurtz, A., Zerva, C., Sindhujan, A., Zouhar, V., Kanojia, D., Blain, F., Thompson, B., Filandrianos, G., Menis Mastromichalakis, O., Kocmi, T., & Gupta, P. (2026). Findings of the WMT26 Shared Task on Automated Translation Quality Evaluation Systems: Compact Open Models are Competitive Quality Evaluators. _Proceedings of the Eleventh Conference on Machine Translation_, 924–1023. Association for Computational Linguistics. https://doi.org/10.18653/2026.wmt-main.49

[3] Deoghare, S., Choudhary, P., Kanojia, D., Ranasinghe, T., Bhattacharyya, P., & Orăsan, C. (2023). A Multi-task Learning Framework for Quality Estimation. _Findings of the Association for Computational Linguistics: ACL 2023_, 9191–9205. Association for Computational Linguistics. https://doi.org/10.18653/v1/2023.findings-acl.585

[4] Geng, X., Lai, Z., Zhang, Y., Tao, S., Yang, H., Chen, J., & Huang, S. (2023). Unify Word-level and Span-level Tasks: NJUNLP’s Participation for the WMT2023 Quality Estimation Shared Task. _Proceedings of the Eighth Conference on Machine Translation_, 829–834. Association for Computational Linguistics. https://doi.org/10.18653/v1/2023.wmt-1.71

[5] Guerreiro, N. M., Rei, R., van Stigt, D., Coheur, L., Colombo, P., & Martins, A. F. T. (2024). xCOMET: Transparent Machine Translation Evaluation through Fine-grained Error Detection. _Transactions of the Association for Computational Linguistics, 12_, 979–995. https://doi.org/10.1162/tacl_a_00683

[6] Kim, A., Park, C., & Kim, S.-H. (2026). FACET at WMT 2026 Automated Translation Quality Evaluation Task. _Proceedings of the Eleventh Conference on Machine Translation_, 1667–1677. Association for Computational Linguistics. https://doi.org/10.18653/2026.wmt-main.100

[7] Siani, A. (2026). Reference-Free Consensus Evaluation of Machine Translation: Ensembling LLM Error-Span Judgments with Neutral Cross-Verification and STAPLE Reliability Fusion. _Proceedings of the Eleventh Conference on Machine Translation_, 1739–1744. Association for Computational Linguistics. https://doi.org/10.18653/2026.wmt-main.108

[8] Silchenko, M. (2026). QEbreak at WMT26: A Pre-Registered Audit of Omission and Addition Asymmetry in Machine Translation Quality Metrics. _Proceedings of the Eleventh Conference on Machine Translation_, 1745–1756. Association for Computational Linguistics. https://doi.org/10.18653/2026.wmt-main.109

[9] Riley, P., Deutsch, D., Finkelstein, M., DiIanni, C., Juraska, J., & Freitag, M. (2026). MQM Re-Annotation: A Technique for Collaborative Evaluation of Machine Translation. _Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_, 33673–33684. Association for Computational Linguistics. https://doi.org/10.18653/v1/2026.acl-long.1553

[10] Liu, S., Dai, G., & Li, D. (2025). Introducing Quality Estimation to Machine Translation Post-editing Workflow: An Empirical Study on Its Usefulness. _Proceedings of Machine Translation Summit XX: Volume 1_, 485–495. European Association for Machine Translation. https://aclanthology.org/2025.mtsummit-1.38/

[11] Proietti, L., Grundkiewicz, R., & Post, M. (2026). PEAR: Pairwise Evaluation for Automatic Relative Scoring in Machine Translation. _Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_, 42189–42207. Association for Computational Linguistics. https://doi.org/10.18653/v1/2026.acl-long.1953

[12] Freitag, M., Foster, G., Grangier, D., Ratnakar, V., Tan, Q., & Macherey, W. (2021). Experts, Errors, and Context: A Large-Scale Study of Human Evaluation for Machine Translation. _Transactions of the Association for Computational Linguistics, 9_, 1460–1474. https://doi.org/10.1162/tacl_a_00437

[13] Lommel, A. R., Burchardt, A., & Uszkoreit, H. (2013). Multidimensional quality metrics: A flexible system for assessing translation quality. _Proceedings of Translating and the Computer 35_. Aslib. https://aclanthology.org/2013.tc-1.6/

[14] Saito, T., & Rehmsmeier, M. (2015). The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets. _PLOS ONE, 10_(3), e0118432. https://doi.org/10.1371/journal.pone.0118432

[15] Chicco, D., & Jurman, G. (2020). The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation. _BMC Genomics, 21_, 6. https://doi.org/10.1186/s12864-019-6413-7

[16] Google. (n.d.). _wmt-mqm-human-evaluation_ [Dataset repository]. GitHub. https://github.com/google/wmt-mqm-human-evaluation

[17] Sindhujan, A., Kanojia, D., & Orăsan, C. (2025). Reference-Less Evaluation of Machine Translation: Navigating Through the Resource-Scarce Scenarios. _Information, 16_(10), 916. https://doi.org/10.3390/info16100916

**Ghi chú về lựa chọn tài liệu:** Các bài năm 2026 được dùng để mô tả xu hướng nghiên cứu và đặt dự án vào bối cảnh hiện tại; không được dùng để ngụ ý nhóm đã triển khai hoặc so sánh thực nghiệm với FACET, PEAR, xCOMET hay hệ thống LLM. Tài liệu tham khảo chỉ nên giữ trong bản nộp nếu có trích dẫn tương ứng trong nội dung. Các bài báo năm 2026 được kiểm tra tại trang ACL Anthology chính thức; các thông tin tác giả, tên bài, venue, trang và DOI được giữ theo metadata xuất bản.

# PHỤ LỤC A. DANH MỤC ARTEFACT THỰC NGHIỆM

Các artefact chính được README dự án ghi nhận:

**Week 10 – Split và QA**

- `results/week10/locked_split/manifest.json`
- `results/week10/locked_split/qa_report.txt`
- `results/week10/locked_split/document_assignments.csv`

**Week 10 – Baseline, ablation và Test**

- `results/week10/baseline_results/dev_baseline_metrics.csv`
- `results/week10/ablation_dev/dev_ablation_metrics.csv`
- `results/week10/ablation_dev/dev_ablation_predictions.csv`
- `results/week10/test_evaluation/test_predictions.csv`
- `results/week10/test_evaluation/test_point_metrics.csv`
- `results/week10/test_evaluation/test_metrics_with_ci.csv`
- `results/week10/test_evaluation/paired_difference_ci.csv`
- `results/week10/test_evaluation/test_audit_notes.md`

**Week 10 – Error analysis**

- `results/week10/error_analysis_dev/dev_top20_zero_vote_segments.csv`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_annotations.csv`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_summary.csv`
- `results/week10/error_analysis_dev/dev_error_analysis_manifest.json`

**Week 11 – Phân tích định tính hiện hành**

- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_cases.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_audit_report.md`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_audit_summary.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_matched_annotations.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_unmatched_annotations.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_qualitative_evidence.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_evidence_manifest.csv`
