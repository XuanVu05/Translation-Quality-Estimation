# PHASE 5 -- XLM-R: Kết quả huấn luyện và đánh giá trên Train/Dev

**Trạng thái: HOÀN THÀNH -- KHÔNG HUẤN LUYỆN THÊM EPOCH 4--5**

**Mô hình:** `FacebookAI/xlm-roberta-base`\
**Dữ liệu:** WMT 2020 MQM English→German -- tập Train/Dev đã được xác
minh ở các giai đoạn trước\
**Phạm vi:** Huấn luyện và lựa chọn checkpoint trên Train/Dev; không
truy cập Test.

---

## 1. Mục tiêu Phase 5

Phase 5 được thực hiện nhằm bổ sung XLM-R (Transformer đa ngôn ngữ) làm
mô hình đối chiếu với các baseline học máy truyền thống của dự án Second
Pair of Eyes -- Reference-Free Critical Error Detection.

Mục tiêu của thí nghiệm:

- Huấn luyện XLM-R trên tập Train đã cố định.
- Theo dõi khả năng tổng quát hóa trên Dev.
- Chọn checkpoint dựa trên Dev PR-AUC (Average Precision).
- Đối chiếu kết quả với các baseline trên cùng tập Dev.
- Không sử dụng Test để lựa chọn epoch, checkpoint hoặc siêu tham số.

Phase 5 không đặt mục tiêu chứng minh XLM-R chắc chắn tốt hơn baseline;
kết quả được dùng để đánh giá mô hình Transformer trong thiết lập hiện
tại.

## 2. Dữ liệu và kiểm tra đầu vào

Notebook xác nhận các tệp đầu vào đúng với dữ liệu đã kiểm tra trước đó.

Thành phần Train Dev

---

Số mẫu 6.797 1.554
Số documents 90 20
Số nhãn dương (y=1) 803 218
Tỷ lệ nhãn dương 11,81% 14,03%
Số hệ thống dịch 7 7

Các kiểm tra trong notebook đều đạt:

- Đủ các cột dữ liệu bắt buộc.
- Nhãn `y_primary` không bị thiếu và chỉ nhận giá trị 0 hoặc 1.
- Source và target không bị thiếu hoặc rỗng.
- Kích thước Train/Dev và số lượng nhãn dương khớp với dữ liệu đã xác
  minh.
- Không có document trùng giữa Train và Dev.

**Kết luận về dữ liệu:** Đầu vào của thí nghiệm khớp với phân chia
Train/Dev được sử dụng trong dự án.

## 3. Cấu hình thí nghiệm

Thành phần Cấu hình

---

Pretrained model `FacebookAI/xlm-roberta-base`
Bài toán Phân loại nhị phân
Đầu vào Cặp Source -- MT Target
Tokenization Tokenizer XLM-R
Maximum sequence length 256
Truncation Bật
Padding Dynamic padding qua `DataCollatorWithPadding`
Số nhãn 2
Loss Weighted Cross-Entropy
Class weights Tính từ nhãn Train
Learning rate 2e-5
Train batch size 8
Evaluation batch size 16
Gradient accumulation 2
Effective train batch size 16
Weight decay 0,01
Số epoch 3
Seed 42
Precision FP16
Optimizer AdamW (`adamw_torch`)
Checkpoint selection Dev PR-AUC
Early stopping Không cấu hình
Test access Không

Thí nghiệm chạy trên Google Colab với GPU NVIDIA Tesla T4 (15 GB bộ nhớ
GPU). Thời gian huấn luyện được ghi nhận là **517,024 giây**, tương
đương khoảng **8,62 phút**.

### Xử lý mất cân bằng lớp

Tập Train có 803 mẫu dương trên tổng số 6.797 mẫu. Notebook sử dụng
`compute_class_weight(class_weight="balanced")` để tính trọng số hai lớp
từ Train, sau đó áp dụng weighted Cross-Entropy.

Không sử dụng nhãn Dev để tính class weights.

## 4. Kết quả theo từng epoch

Checkpoint được đánh giá ở cuối mỗi epoch. Các chỉ số Dev được ghi nhận:

---

Chỉ số Epoch 1 -- step Epoch 2 -- step Epoch 3 -- step
425 850 1275

---

Evaluation loss 0,757186 0,874378 1,279431

Dev PR-AUC / 0,175143 **0,201489** 0,179628
Average  
 Precision

Dev ROC-AUC 0,542218 **0,645807** 0,553897

Precision@0.5 0,200000 **0,258503** 0,254717

Recall@0.5 0,013761 **0,174312** 0,123853

MCC@0.5 0,016976 **0,110033** 0,089154

---

Epoch 2 đạt kết quả tốt nhất trên cả sáu chỉ số được ghi nhận tại thời
điểm đánh giá cuối epoch. Vì tiêu chí lựa chọn checkpoint đã được xác
định là `eval_pr_auc`, **checkpoint tốt nhất là `checkpoint-850` (epoch 2)**.

### 4.1. Diễn biến từ Epoch 1 đến Epoch 2

Dev PR-AUC tăng từ 0,175143 lên 0,201489. ROC-AUC tăng từ 0,542218 lên
0,645807. Precision@0.5, Recall@0.5 và MCC@0.5 cũng tăng.

Kết quả cho thấy mô hình cải thiện khả năng xếp hạng và phân biệt hai
lớp trong giai đoạn từ epoch 1 đến epoch 2.

### 4.2. Diễn biến từ Epoch 2 đến Epoch 3

Dev PR-AUC giảm từ 0,201489 xuống 0,179628. ROC-AUC giảm từ 0,645807
xuống 0,553897. Recall@0.5 giảm từ 0,174312 xuống 0,123853; MCC@0.5 giảm
từ 0,110033 xuống 0,089154.

Đồng thời, evaluation loss tăng từ 0,874378 lên 1,279431. Như vậy, dù
quá trình tối ưu trên Train tiếp tục diễn ra, hiệu quả trên Dev suy giảm
ở epoch 3.

Diễn biến này là **dấu hiệu phù hợp với hiện tượng overfitting** trong
thiết lập hiện tại. Với kết quả quan sát được, không có cơ sở thực
nghiệm để kỳ vọng việc tiếp tục epoch 4--5 với cùng cấu hình sẽ cải
thiện khả năng tổng quát hóa.

## 5. Kết quả XLM-R tốt nhất trên Dev

Sử dụng checkpoint epoch 2 (`checkpoint-850`), kết quả đánh giá trên
Dev:

---

Chỉ số Giá trị

---

Số mẫu Dev 1.554

Số mẫu dương 218

Prevalence 0,140283

Average Precision (AP; PR-AUC **0,201489**
theo quy ước báo cáo của dự  
 án)

ROC-AUC **0,645807**

Precision@0.5 0,258503

Recall@0.5 0,174312

MCC@0.5 0,110033

---

Các chỉ số Precision@0.5, Recall@0.5 và MCC@0.5 được tính tại ngưỡng xác
suất 0,5. Chúng **không phải** Precision@20%, Recall@20% hoặc
MCC@top20%.

## 6. Đối chiếu với các baseline trên Dev

Kết quả XLM-R được đặt cạnh các baseline đã đánh giá trên cùng tập Dev.
LR_Base là Logistic Regression sử dụng TF-IDF Source/Target và 12 đặc
trưng bề mặt.

---

Mô hình AP / PR-AUC Precision@20% Recall@20% Lift@20% MCC@top20%

---

Logistic 0,1961 0,2026 0,2890 1,4440 0,0897
Regression --  
 LR_Base

Logistic 0,1991 0,1961 0,2798 1,3982 0,0805
Regression --  
 LR_Plus_System

System_Only 0,1568 0,1768 0,2523 1,2607 0,0527

XLM-R -- epoch 2 **0,2015** Chưa xác nhận Chưa xác Chưa xác Chưa xác
nhận nhận nhận

---

XLM-R có AP cao nhất trong các mô hình được liệt kê, nhưng mức chênh
lệch so với LR_Base nhỏ: 0,201489 so với 0,1961, chênh lệch khoảng
0,0054.

Chưa thể kết luận XLM-R tốt hơn Logistic Regression trong mục tiêu vận
hành top-20%, vì các chỉ số top-20% của XLM-R chưa được xác nhận từ bảng
dự đoán trong log được cung cấp. Không so sánh Recall@0.5 của XLM-R với
Recall@20% của LR_Base vì đây là hai chỉ số khác nhau.

**Nhận định:** XLM-R có AP trên Dev nhỉnh hơn LR_Base ở mức điểm ước
lượng. Tuy nhiên, chênh lệch nhỏ và chưa có kiểm định thống kê; kết quả
hiện tại chưa chứng minh XLM-R vượt trội về hiệu quả vận hành.

### XLM-R Evaluation on the Canonical Test Set

Mô hình XLM-RoBERTa-base được đánh giá trên tập Test chính thức gồm 1.575 mẫu, trong đó có 162 mẫu dương tính, tương ứng tỷ lệ 10,29%. Checkpoint `checkpoint-850` (Epoch 2), được lựa chọn dựa trên Average Precision trên tập Development (Dev AP = 0,201489), được sử dụng cho quá trình suy luận. Quá trình inference được thực hiện trên GPU Tesla T4, với thời gian xử lý khoảng 14,04 giây.

Trên tập Test, XLM-R đạt Average Precision (AP) = 0,1496 và ROC-AUC = 0,6483. Khi đánh giá theo ngân sách rà soát cố định Top 20%, mô hình đạt Precision@20% = 0,2032, Recall@20% = 0,3951, Lift@20% = 1,9753 và MCC@Top20% = 0,1651. Cụ thể, trong 315 bản dịch được ưu tiên rà soát, mô hình phát hiện 64 trong tổng số 162 mẫu được gán nhãn lỗi nghiêm trọng.

So với Logistic Regression, XLM-R có AP thấp hơn (0,1496 so với 0,1971), nhưng đạt kết quả tốt hơn trên các chỉ số vận hành Top 20%. Recall@20% tăng từ 31,48% lên 39,51%, trong khi Precision@20% tăng từ 16,19% lên 20,32%. Kết quả này cho thấy XLM-R có tiềm năng cải thiện khả năng ưu tiên các bản dịch chứa lỗi nghiêm trọng trong điều kiện ngân sách rà soát hạn chế. Tuy nhiên, sự khác biệt giữa AP và các chỉ số Top 20% cũng cho thấy hiệu quả của mô hình phụ thuộc vào tiêu chí đánh giá và mục tiêu triển khai.

Nhìn chung, XLM-R không thay thế hoàn toàn Logistic Regression trên mọi khía cạnh. Logistic Regression vẫn đạt Average Precision cao nhất, trong khi XLM-R đạt hiệu quả tốt nhất tại vùng Top 20% theo các chỉ số Precision, Recall, Lift và MCC. Do đó, hai mô hình đại diện cho hai đặc tính khác nhau: khả năng xếp hạng tổng thể và khả năng ưu tiên phát hiện lỗi trong ngân sách rà soát cố định.

**Lưu ý về tính hợp lệ của đánh giá:** Kết quả trên là đánh giá inference của checkpoint đã được lựa chọn bằng Dev, không phải kết quả huấn luyện hoặc lựa chọn mô hình trên Test. Tuy nhiên, lịch sử Git cho thấy các dự đoán và metrics Test đã xuất hiện trong commit đầu tiên của dự án trước khi manifest split được bổ sung. Vì vậy, chưa thể khẳng định tập Test hoàn toàn chưa từng được tiếp xúc trong lịch sử phát triển. Hạn chế này cần được công khai khi diễn giải kết quả thực nghiệm.

## 7. Quyết định về số epoch

**Quyết định: Dừng huấn luyện ở 3 epoch và sử dụng checkpoint epoch 2.
Không chạy epoch 4--5 trong thí nghiệm hiện tại.**

Cơ sở quyết định:

1.  Epoch 2 có Dev PR-AUC cao nhất: 0,201489.
2.  Epoch 3 làm giảm PR-AUC, ROC-AUC, Recall@0.5 và MCC@0.5.
3.  Evaluation loss tăng đáng kể ở epoch 3.
4.  Notebook cấu hình `load_best_model_at_end=True` và
    `metric_for_best_model="eval_pr_auc"`, do đó Trainer khôi phục
    checkpoint tốt nhất theo Dev PR-AUC.
5.  Không có bằng chứng trong log hiện tại cho thấy epoch 4--5 sẽ cải
    thiện kết quả.

Đây là quyết định dừng hợp lý theo tiêu chí đã đặt ra, không phải khẳng
định rằng mọi cấu hình XLM-R khác đều không thể cải thiện.

## 8. Tệp đầu ra và khả năng tái lập

Notebook đã lưu các đầu ra trong:

`My Drive/MLA_Phase5_XLMR/outputs/`

---

Tệp / thư mục Nội dung

---

`checkpoints/checkpoint-425/` Trạng thái checkpoint sau epoch 1

`checkpoints/checkpoint-850/` Trạng thái checkpoint sau epoch 2

`checkpoints/checkpoint-1275/` Trạng thái checkpoint sau epoch 3

`best_model/` Mô hình tốt nhất được lưu sau khi
Trainer khôi phục checkpoint tốt
nhất

`dev_predictions_xlmr.csv` Dự đoán và score XLM-R cho 1.554
mẫu Dev

`dev_metrics_xlmr.json` Các chỉ số đánh giá Dev

`training_summary.json` Cấu hình, thời gian huấn luyện,
checkpoint tốt nhất và thông tin
phạm vi dữ liệu

`training_log_history.csv` Lịch sử loss, learning rate và các
chỉ số đánh giá theo step/epoch

---

Thời gian huấn luyện trong log là khoảng 517 giây. Notebook xác nhận đã
lưu 1.554 dự đoán Dev và không tạo tệp `test_predictions_xlmr.csv`.

## 9. Giới hạn cần nêu trong báo cáo

- Kết quả XLM-R mới được đánh giá trên một tập Dev gồm 20 documents;
  độ ổn định theo nhiều seed chưa được kiểm tra.
- Kết quả là điểm ước lượng trên một lần chạy với seed 42; chưa có
  khoảng tin cậy bootstrap cho XLM-R.
- Dev PR-AUC của XLM-R chỉ nhỉnh hơn LR_Base một khoảng nhỏ; chưa có
  kiểm định thống kê để khẳng định khác biệt.
- Các chỉ số top-20% của XLM-R cần được lấy trực tiếp từ
  `dev_predictions_xlmr.csv` nếu cần báo cáo kết quả vận hành.
- Test chưa được sử dụng trong Phase 5. Do đó, chưa có kết quả XLM-R
  trên Test và chưa thể đưa ra kết luận về hiệu năng cuối cùng trên
  tập giữ kín.
- Kết quả epoch 3 cho thấy dấu hiệu overfitting; kết luận này được
  giới hạn trong cấu hình và lần chạy hiện tại.

## 10. Kết luận Phase 5

Phase 5 đã hoàn thành mục tiêu huấn luyện và đánh giá XLM-R trên
Train/Dev. Mô hình `FacebookAI/xlm-roberta-base` được huấn luyện trong 3
epoch trên Google Colab GPU Tesla T4. Checkpoint tốt nhất theo tiêu chí
Dev PR-AUC là `checkpoint-850` tại epoch 2, đạt AP = 0,201489 và ROC-AUC
= 0,645807.

Khi chuyển từ epoch 2 sang epoch 3, các chỉ số Dev suy giảm và
evaluation loss tăng. Vì vậy, nhóm dừng thí nghiệm tại đây, không tiếp
tục epoch 4--5 với cùng cấu hình. XLM-R có AP trên Dev nhỉnh hơn LR_Base
ở mức điểm ước lượng, nhưng chưa có bằng chứng để khẳng định mô hình
vượt trội trong mục tiêu vận hành top-20%.

**Trạng thái cuối cùng: PHASE 5 -- COMPLETED (TRAIN/DEV EXPERIMENT).**\
**Checkpoint được chọn: `checkpoint-850` (Epoch 2).**\
**Test set: NOT ACCESSED.**\
**Không thực hiện huấn luyện bổ sung epoch 4--5 trong Phase 5 hiện
tại.**

---

_Ghi chú thuật ngữ: `average_precision_score` được gọi là Average
Precision (AP), đồng thời ghi chú PR-AUC theo quy ước báo cáo của dự án.
AP không đồng nhất với diện tích PR curve tính bằng quy tắc hình thang._
