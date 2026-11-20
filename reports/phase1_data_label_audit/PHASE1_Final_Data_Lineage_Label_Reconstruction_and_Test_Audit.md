# PHASE 1 --- DATA LINEAGE, LABEL RECONSTRUCTION, DATA SPLIT AND TEST-SET AUDIT

**Dự án:** Second Pair of Eyes --- Reference-Free Critical Error
Detection\
**Dữ liệu:** WMT 2020 MQM English--German (`newstest2020`)\
**Phạm vi:** Kiểm tra nguồn dữ liệu, tái dựng nhãn, căn chỉnh source,
phân chia dữ liệu, luồng tiền xử lý và tính toàn vẹn của Test\
**Ngày hoàn thiện:** 20/11/2026\
**Trạng thái:** **Completed with documented limitations**

------------------------------------------------------------------------

## 1. Mục tiêu và phạm vi

Phase 1 nhằm xác lập và kiểm tra khả năng truy xuất nguồn gốc dữ liệu
(data lineage) cho bài toán phát hiện lỗi dịch thuật nghiêm trọng không
cần văn bản tham chiếu (Reference-Free Critical Error Detection). Các
nội dung được kiểm tra gồm:

1.  Xác định nguồn MQM và MT output gốc; kiểm tra cách đọc dữ liệu và bộ
    lọc hệ thống dịch.
2.  Tái dựng độc lập nhãn nghiêm trọng ở cấp segment từ các annotation
    MQM.
3.  Kiểm tra khóa định danh và căn chỉnh source segment với dữ liệu WMT
    chính thức.
4.  Kiểm tra cách chia Train/Dev/Test theo document và mức độ tách biệt
    giữa các tập.
5.  Kiểm tra đường đi của dữ liệu đầu vào mô hình, đặc biệt là reviewer
    markup `<v>` và `</v>`.
6.  Kiểm tra các artifact và lịch sử Git liên quan đến split và đánh giá
    Test, đồng thời ghi nhận giới hạn của bằng chứng lịch sử.

Phase 1 là hoạt động kiểm toán dữ liệu và quy trình. Không huấn luyện mô
hình mới, không điều chỉnh ngưỡng, không lựa chọn mô hình bằng Test và
không chạy lại đánh giá Test trong quá trình hoàn tất các kiểm tra được
mô tả ở đây.

## 2. Nguồn dữ liệu và quy mô

### 2.1. MQM annotation data

Dữ liệu MQM gốc chứa **79.024 dòng annotation** và bao gồm 10 MT
systems. Sau khi giữ lại 7 hệ thống được sử dụng trong nghiên cứu, dữ
liệu còn **61.120 dòng annotation**.

Một sai lệch trước đây giữa con số 79.020 và 79.024 đã được giải thích
bằng hành vi phân tích CSV. Khi dùng parser quote-aware thông thường,
một số dấu ngoặc kép xuất hiện trong nội dung annotation bị hiểu nhầm là
ký tự bao vùng dữ liệu, dẫn đến việc gộp bốn cặp dòng vật lý và làm giảm
số dòng được đọc. Đọc tệp với `csv.QUOTE_NONE` (`quoting=3`) cho kết quả
79.024 dòng phù hợp với cấu trúc dữ liệu được kiểm tra.

Ba bản sao của tệp MQM được đối chiếu có cùng SHA-256:

`22ACB4D5CC4DC0D8F2683E9251C179C917AE8589D71B1945D755C46D88D345E3`

Do đó, chênh lệch 79.020/79.024 được xác định là vấn đề cách phân tích
dữ liệu, không phải bằng chứng cho thấy các bản dữ liệu khác nhau.

### 2.2. Tập segment ở cấp bản dịch

Tập dữ liệu mô hình có các đặc điểm:

  Thuộc tính                                                 Giá trị
  ----------------------------------------- ------------------------
  Số MT systems                                                    7
  Số documents                                                   130
  Số source segments                                           1.418
  Số translation segments                                      9.926
  Số MQM annotation rows sau lọc                              61.120
  Số rater đánh giá trong toàn bộ dữ liệu     6 (`rater1`--`rater6`)
  Số đánh giá cho mỗi translation segment                          3

Mỗi translation segment được định danh theo tổ hợp khóa hệ
thống/document/segment, bao gồm `system`, `doc`, `doc_id` và `seg_id`.
Mỗi segment có ba đánh giá rater tương ứng.

## 3. Quy tắc xây dựng nhãn nghiêm trọng

### 3.1. Định nghĩa serious annotation

Một annotation được tính là một phiếu lỗi nghiêm trọng khi đồng thời
thỏa mãn:

-   `severity == "Major"`; và
-   `category` bắt đầu bằng `Accuracy/` hoặc bằng chính xác
    `Non-translation!`.

Các annotation không thỏa mãn đồng thời hai điều kiện trên không được
tính là serious vote trong định nghĩa nhãn chính.

### 3.2. Tổng hợp phiếu theo rater và nhãn nhị phân

Quy trình tổng hợp được thực hiện theo từng translation segment:

1.  Gom annotation theo `system/doc/doc_id/seg_id/rater`.
2.  Mỗi rater đóng góp tối đa một serious vote cho một translation
    segment; nếu có nhiều annotation phù hợp, lấy giá trị tối đa cho
    rater đó.
3.  Cộng phiếu của ba rater để tạo `serious_votes`.
4.  Đặt `y_primary = 1` nếu `serious_votes >= 2`; ngược lại
    `y_primary = 0`.

Đây là quy tắc majority vote 2/3, không phải quy tắc chỉ cần một
annotation Major là gán nhãn dương.

### 3.3. Phân phối nhãn và phiếu

    Serious votes   Số segment
  --------------- ------------
              0/3        6.810
              1/3        1.933
              2/3          846
              3/3          337
         **Tổng**    **9.926**

Phân phối nhãn nhị phân:

  Nhãn                Số segment      Tỷ lệ
  ----------------- ------------ ----------
  `y_primary = 0`          8.743     88,08%
  `y_primary = 1`          1.183     11,92%
  **Tổng**             **9.926**   **100%**

Dữ liệu có mất cân bằng lớp: tỷ lệ positive là 11,92%. Đây là đặc điểm
cần được tính đến khi diễn giải các chỉ số đánh giá và thiết kế thí
nghiệm tiếp theo.

## 4. Tái dựng nhãn độc lập

Để xác minh nhãn không chỉ dựa trên artifact đã xây dựng, toàn bộ nhãn
được tái dựng độc lập từ raw MQM annotation bằng cùng định nghĩa serious
annotation và quy tắc tổng hợp rater nêu trên.

### 4.1. Kết quả đối chiếu

  Hạng mục                                 Kết quả
  -------------------------------------- ---------
  Raw MQM records được đọc                  79.024
  Annotation rows sau lọc 7 systems         61.120
  Số segment trong dataset hiện tại          9.926
  Số segment tái dựng độc lập                9.926
  Số khóa khớp                               9.926
  Chỉ xuất hiện trong dataset hiện tại           0
  Chỉ xuất hiện trong dữ liệu tái dựng           0
  Khóa trùng trong dataset hiện tại              0
  Khóa trùng trong dữ liệu tái dựng              0
  Sai khác `distinct_raters`                     0
  Sai khác `serious_votes`                       0
  Sai khác `y_primary`                           0
  Segment không có đúng 3 rater                  0

Phân phối được tái dựng độc lập cũng khớp hoàn toàn:

-   `y=0`: 8.743; `y=1`: 1.183.
-   0 serious votes: 6.810; 1 vote: 1.933; 2 votes: 846; 3 votes: 337.

### 4.2. Kết luận

**PASS.** Tất cả 9.926 segment đều khớp theo khóa định danh, số rater,
số serious votes và nhãn nhị phân. Không phát hiện segment thiếu/thừa,
khóa trùng hoặc sai khác nhãn trong phép đối chiếu độc lập.

Kết quả này xác nhận việc xây dựng `y_primary` nhất quán với quy tắc
serious annotation đã công bố và được áp dụng trên toàn bộ tập dữ liệu.

## 5. Source alignment và kiểm tra định danh segment

Source được đối chiếu với metadata và tệp source chính thức của WMT
2020.

### 5.1. Ánh xạ khóa

Trong `data/details/en-de.txt`, các trường được sử dụng gồm `line_id`,
`set_id`, `language_pair`, `document_id` và `segment_id`. Ánh xạ khóa
giữa MQM và metadata được xác định như sau:

  MQM        Metadata
  ---------- ---------------
  `doc`      `document_id`
  `seg_id`   `line_id`
  `doc_id`   `segment_id`

Toàn bộ 1.418 source-segment keys được đối chiếu với metadata.

### 5.2. Đối chiếu source chính thức

Tệp source chính thức được kiểm tra là:

`data/official_wmt2020/sgm/newstest2020-ende-src.en.sgm`

XML parser thông thường không xử lý được tệp do có ký tự XML không hợp
lệ. Vì vậy, nội dung được trích xuất bằng phương pháp regex phù hợp với
cấu trúc tệp, sau đó kiểm tra số document, số segment và thứ tự.

Kết quả:

-   Khôi phục 130 documents.
-   Khôi phục 1.418 source segments.
-   Số lượng và thứ tự segment phù hợp với metadata.
-   Sau chuẩn hóa NFC, khoảng trắng và dấu ngoặc kép, các chuỗi được căn
    chỉnh.
-   954 segment khớp chính xác sau chuẩn hóa.
-   464 trường hợp chỉ khác định dạng dấu ngoặc kép.

Do đó, source alignment được xác nhận ở mức cấu trúc và nội dung sau
chuẩn hóa. Không nên mô tả kết quả này là byte-identical giữa mọi chuỗi
source.

## 6. Mức độ đồng thuận giữa rater

Trong 9.926 translation segments:

-   7.147 segment có đồng thuận tuyệt đối giữa ba rater.
-   2.779 segment có bất đồng (phân bố phiếu 1/2 hoặc 2/1).
-   Tỷ lệ đồng thuận tuyệt đối xấp xỉ 72%.
-   Fleiss' Kappa = **0,290029**.

Theo cách diễn giải heuristic Landis--Koch, giá trị này thường được xếp
vào mức "fair"; đây chỉ là quy ước diễn giải tham khảo, không phải
ngưỡng đánh giá phổ quát.

Tỷ lệ serious vote gộp theo rater có khác biệt. Tuy nhiên, không thể kết
luận rater có thiên lệch chỉ từ khác biệt tỷ lệ phiếu. Ngoài ra, cùng
một tổ hợp ba rater được sử dụng cho các hệ thống dịch trên cùng source
segment; việc phân công rater theo document do đó gắn với đặc điểm
document. Đây là một yếu tố cần lưu ý khi diễn giải phân tích theo rater
và document.

## 7. Chiến lược chia Train/Dev/Test

### 7.1. Phương pháp

Tệp `src/split_by_document.py` sử dụng `GroupShuffleSplit` với document
làm group, nhằm tránh các translation segments thuộc cùng document xuất
hiện ở nhiều tập.

Quy trình được ghi nhận:

1.  Tách Test trước, sử dụng `random_state=42`, với tỷ lệ mục tiêu 15%.
2.  Từ phần dữ liệu còn lại, tách Dev bằng `random_state=43`, với tỷ lệ
    15% của phần còn lại.
3.  Phần còn lại được sử dụng làm Train.

Tỷ lệ cuối cùng xấp xỉ 70/15/15 theo số document.

### 7.2. Quy mô từng tập

  ----------------------------------------------------------------------------
  Tập           Documents       Source   Translation     Positive     Positive
                              segments          rows         rows         rate
  ---------- ------------ ------------ ------------- ------------ ------------
  Train                90          971         6.797          803       11,81%

  Dev                  20          222         1.554          218       14,03%

  Test                 20          225         1.575          162       10,29%

  **Tổng**        **130**    **1.418**     **9.926**    **1.183**   **11,92%**
  ----------------------------------------------------------------------------

Không phát hiện document overlap giữa Train, Dev và Test.

Các artifact split được kiểm tra về khóa, missing values và duplicate
`system/doc/seg_id` keys; không phát hiện vấn đề trong các kiểm tra này.

### 7.3. Trạng thái khóa split

Manifest ghi trạng thái `candidate_locked`. Trạng thái này thể hiện một
split ứng viên đã được ghi nhận, nhưng bản thân nó không chứng minh rằng
split đã được khóa trước tất cả hoạt động thử nghiệm hoặc lựa chọn mô
hình.

Không tìm thấy lý do lịch sử đầy đủ giải thích tại sao split này được
chọn tại thời điểm tạo. Vì vậy, báo cáo chỉ xác nhận cấu trúc và tính
tách biệt của split hiện có, không khẳng định được toàn bộ lịch sử ra
quyết định trước thực nghiệm.

## 8. Reviewer markup và nguồn dữ liệu đầu vào mô hình

### 8.1. Rủi ro cần kiểm tra

MQM annotation target có thể chứa reviewer markup như `<v>` và `</v>`.
Nếu các marker này lọt vào target dùng làm đầu vào mô hình, mô hình có
thể học từ dấu vết của quy trình annotation thay vì chỉ từ nội dung bản
dịch máy.

Do đó, cần xác định chính xác target được lấy từ đâu và kiểm tra dữ liệu
thực tế ở cả master dataset lẫn các split.

### 8.2. Truy vết trong mã nguồn

Kiểm tra `src/build_model_dataset.py` cho thấy:

-   Raw MQM được sử dụng để xác định annotation, serious votes và nhãn.
-   Target dùng cho model dataset được đọc từ các tệp MT output gốc có
    dạng `original_outputs/newstest2020.en-de.<system>.txt`.
-   Dòng target được gán từ bản dịch gốc tương ứng với vị trí segment.
-   Builder không lấy trực tiếp MQM annotated target làm trường `target`
    của model dataset.
-   Không có bước strip reviewer markup trong đường tạo target này, bởi
    target đầu vào được lấy từ original MT outputs.

Kiểm tra `src/run_baselines.py` cho thấy baseline đọc `source` và
`target` từ Train/Dev, sau đó sử dụng trực tiếp các trường này trong các
đặc trưng văn bản và TF-IDF. TF-IDF được fit trên Train và transform
trên Dev. Không thấy bước xóa `<v>`/`</v>` trong baseline pipeline.

### 8.3. Kiểm tra trực tiếp các dataset

Kiểm tra read-only trên các file sau:

-   `results/week10/model_data/mt_segment_level_original_outputs.csv`
-   `results/week10/model_data/train_segments.csv`
-   `results/week10/model_data/dev_segments.csv`
-   `results/week10/model_data/test_segments.csv`

Kết quả kiểm tra cả hai trường `source` và `target`:

  ----------------------------------------------------------------------------
  Dataset           Rows        Marker  Rows bị ảnh        Marker  Rows bị ảnh
                           occurrences  hưởng trong   occurrences  hưởng trong
                          trong source       source  trong target       target
  --------- ------------ ------------- ------------ ------------- ------------
  MASTER           9.926             0            0             0            0

  TRAIN            6.797             0            0             0            0

  DEV              1.554             0            0             0            0

  TEST             1.575             0            0             0            0
  ----------------------------------------------------------------------------

### 8.4. Kết luận

**PASS.** Không phát hiện `<v>` hoặc `</v>` trong source/target của
master dataset, Train, Dev hoặc Test.

Kết luận cần diễn đạt chính xác: pipeline tránh reviewer markup bằng
việc sử dụng original MT outputs thay vì MQM annotated target. Đây là
lựa chọn nguồn dữ liệu ở upstream, không phải một bước loại bỏ marker
trong baseline TF-IDF pipeline.

## 9. Kiểm tra quy trình tiền xử lý và Test

### 9.1. Baseline development pipeline

Kiểm tra `src/run_baselines.py` cho thấy:

-   Đọc `train_segments.csv` và `dev_segments.csv`.
-   Không nạp Test trong luồng phát triển baseline được kiểm tra.
-   TF-IDF vectorizers được fit trên Train và transform trên Dev.
-   `StandardScaler` được fit trên Train và transform trên Dev.
-   Các đặc trưng bề mặt sử dụng source/target, độ dài, chữ số, dấu câu,
    token lặp và chỉ báo target rỗng.

Không chạy lại script trong audit chỉ để kiểm tra, vì script có thao tác
ghi artifact đầu ra.

### 9.2. Test evaluation pipeline

`src/evaluate_test_week10.py` được kiểm tra như một artifact đánh giá đã
tồn tại. Quy trình ghi nhận là fit vectorizer/scaler và mô hình trên
Train+Dev, sau đó đánh giá trên Test. Các dự đoán Test đã lưu được đối
chiếu với split keys và labels.

Không chạy lại script, không tái tạo dự đoán, không điều chỉnh ngưỡng và
không lựa chọn mô hình dựa trên Test trong quá trình hoàn thiện Phase 1.

### 9.3. Giới hạn về tính toàn vẹn lịch sử Test

Kiểm tra Git cho thấy:

-   Repository có 19 commits tại thời điểm audit.
-   Commit đầu tiên: `fbea822`, ngày 27/10/2026 22:18:38.
-   Artifact dự đoán Test và các point metrics đã xuất hiện trong commit
    đầu tiên.
-   Manifest và document assignments xuất hiện trong commit ngày
    29/10/2026; manifest ghi `created_at_utc` ngày 28/10/2026 10:42 UTC.
-   Snapshot split được thêm sau đó; các kiểm tra hash cho thấy file
    split đã được ghi nhận và không thay đổi trong các mốc commit được
    kiểm tra.
-   Script đánh giá Test đã tồn tại trong commit đầu tiên; các thay đổi
    sau đó được ghi nhận chủ yếu liên quan đến đường dẫn dự án.
-   Git timestamps cho biết thời điểm artifact được commit, không chứng
    minh chính xác thời điểm dữ liệu được tạo, chạy, xem hoặc sử dụng
    trong quyết định nghiên cứu.

Vì vậy, **không thể chứng minh chỉ từ Git history rằng Test chưa từng
được xem hoặc sử dụng để lựa chọn mô hình trước khi split được ghi
nhận/khóa**. Đây là giới hạn lịch sử cần công khai, không phải bằng
chứng rằng đã có leakage.

## 10. Các giới hạn và rủi ro còn lại

1.  **Lịch sử khóa split:** manifest mang trạng thái `candidate_locked`;
    không có đủ bằng chứng để xác nhận split được khóa trước mọi hoạt
    động thực nghiệm.
2.  **Lịch sử sử dụng Test:** Git history không thể xác minh đầy đủ việc
    Test có từng được xem xét trong quá trình phát triển trước đó hay
    không.
3.  **Lý do chọn split:** chưa có ghi chép đầy đủ về lý do lịch sử lựa
    chọn chính xác tập document và seed.
4.  **Rater agreement:** Fleiss' Kappa ở mức 0,290029 cho thấy đồng
    thuận không cao; nhãn majority vote vẫn có thể phản ánh bất đồng
    giữa người đánh giá.
5.  **Class imbalance:** positive rate là 11,92%; các metric và kết luận
    vận hành cần được diễn giải trong bối cảnh này.
6.  **Source normalization:** 464 trường hợp chỉ khác định dạng dấu
    ngoặc kép sau chuẩn hóa; không nên tuyên bố mọi source string
    byte-identical.
7.  **Phạm vi audit:** các kiểm tra xác nhận tính nhất quán của artifact
    và pipeline được kiểm tra; không thay thế cho một quy trình
    adjudication ngôn ngữ độc lập bởi chuyên gia dịch thuật.

## 11. Kết luận Phase 1

Phase 1 đã hoàn thành các kiểm tra chính về data lineage, label
reconstruction, source alignment, document-level split, reviewer markup
và các artifact đánh giá hiện có.

Các bằng chứng quan trọng nhất:

-   79.024 raw MQM annotation rows được xác định bằng cách đọc phù hợp
    với cấu trúc dữ liệu.
-   61.120 annotation rows còn lại sau lọc 7 MT systems.
-   9.926/9.926 segment được tái dựng độc lập và khớp hoàn toàn về khóa,
    rater count, serious votes và nhãn.
-   1.418 source segments được đối chiếu với metadata và source chính
    thức; sai khác định dạng được ghi nhận rõ.
-   Train/Dev/Test được chia theo document, không có document overlap.
-   Không phát hiện reviewer markup `<v>` hoặc `</v>` trong MASTER,
    Train, Dev hoặc Test.
-   Baseline development pipeline fit vectorizer/scaler trên Train và
    transform trên Dev.
-   Test evaluation artifacts đã được kiểm tra mà không chạy lại đánh
    giá Test.

**Trạng thái cuối cùng: COMPLETED WITH DOCUMENTED LIMITATIONS.**

Phase 1 đủ cơ sở để chuyển sang giai đoạn nghiên cứu tiếp theo, với điều
kiện các giới hạn liên quan đến lịch sử khóa split và việc sử dụng Test
trong quá khứ được giữ nguyên trong báo cáo và không bị diễn giải thành
bằng chứng rằng Test đã được bảo vệ tuyệt đối từ đầu.

------------------------------------------------------------------------

## Appendix A --- Các tệp và mã nguồn chính được kiểm tra

-   `src/build_model_dataset.py`
-   `src/split_by_document.py`
-   `src/run_baselines.py`
-   `src/run_ablation_dev.py`
-   `src/evaluate_test_week10.py`
-   `data/details/en-de.txt`
-   `data/official_wmt2020/sgm/newstest2020-ende-src.en.sgm`
-   `results/week10/model_data/mt_segment_level_original_outputs.csv`
-   `results/week10/model_data/train_segments.csv`
-   `results/week10/model_data/dev_segments.csv`
-   `results/week10/model_data/test_segments.csv`
-   Split manifest, split snapshot và các artifact Test evaluation được
    lưu trong repository.

## Appendix B --- Nguyên tắc bảo toàn Test

Trong các giai đoạn tiếp theo:

-   Không dùng Test để chọn mô hình, siêu tham số, ngưỡng hoặc chiến
    lược xử lý mất cân bằng.
-   Không huấn luyện lại hoặc tái chấm điểm Test nếu chưa có phê duyệt
    rõ ràng.
-   Phát triển và lựa chọn mô hình trên Train/Dev.
-   Chỉ sử dụng Test cho đánh giá cuối cùng theo một giao thức đã xác
    định trước và ghi nhận đầy đủ.
