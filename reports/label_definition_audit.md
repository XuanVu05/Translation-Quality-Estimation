# G1.3 – Audit định nghĩa nhãn Critical Error

**Trạng thái:** Hoàn thành kiểm tra logic cốt lõi; cần lưu cùng mã kiểm toán độc lập để tăng khả năng tái lập.  
**Phạm vi:** 9.926 phân đoạn đầu ra của 7 hệ thống dịch máy trong tập WMT 2020 MQM English→German.  
**Nguồn chính:** `src/build_model_dataset.py`; đối chiếu với `experiments/week10_priority2_3.py` và dữ liệu MQM gốc.

## 1. Mục tiêu kiểm toán

G1.3 kiểm tra liệu nhãn nhị phân `y_primary` có được xây dựng nhất quán từ các chú giải MQM hay không, đặc biệt ở ba điểm: định nghĩa lỗi nghiêm trọng, cách tổng hợp nhiều annotation của cùng một người chấm, và ngưỡng biểu quyết giữa các người chấm.

## 2. Định nghĩa nhãn được triển khai

Một annotation được xem là lỗi nghiêm trọng nếu đồng thời thỏa mãn:

- `severity == "Major"`; và
- `category` bắt đầu bằng `Accuracy/` hoặc bằng chính xác `Non-translation!`.

Có thể biểu diễn:

```python
is_serious_error = (
    mqm["severity"].eq("Major")
    & (
        mqm["category"].str.startswith("Accuracy/", na=False)
        | mqm["category"].eq("Non-translation!")
    )
)
```

Quy tắc này giới hạn nhãn Critical Error vào lỗi nghiêm trọng về độ chính xác/ngữ nghĩa và lỗi không dịch. Các lỗi Major thuộc những nhóm khác, chẳng hạn Fluency hoặc Style, không tự động được xếp vào lớp Critical theo định nghĩa hiện tại.

## 3. Quy trình tổng hợp nhãn

Đơn vị biểu quyết là một người chấm trên một phân đoạn của một hệ thống dịch:

1. Với mỗi khóa `(system, doc, doc_id, seg_id, rater)`, lấy `max(serious_error_row)`. Như vậy, một người chấm chỉ đóng góp tối đa một phiếu nghiêm trọng cho một phân đoạn, kể cả khi người đó tạo nhiều annotation hoặc nhiều span lỗi.
2. Với mỗi phân đoạn `(system, doc, doc_id, seg_id)`, đếm số phiếu nghiêm trọng từ các người chấm khác nhau.
3. Gán `y_primary = 1` khi `serious_votes >= 2`; ngược lại gán `y_primary = 0`.

Đây là quy tắc đa số tối thiểu 2/3, không phải quy tắc “chỉ cần một annotation Major”. Nó giảm ảnh hưởng của việc một người chấm đánh dấu nhiều span và yêu cầu ít nhất hai người chấm độc lập cùng xác nhận lỗi nghiêm trọng.

## 4. Kết quả kiểm tra trên tập dữ liệu mô hình

| Chỉ tiêu | Kết quả |
|---|---:|
| Số phân đoạn MT | 9.926 |
| Số hệ thống MT | 7 |
| Số khóa phân đoạn duy nhất | 9.926 |
| Phân đoạn có 3 người chấm | 9.926 (100%) |
| Phân đoạn có số người chấm khác 3 | 0 |
| Khóa phân đoạn trùng lặp trong bảng mô hình | 0 |
| Nhãn không Critical (`y=0`) | 8.743 |
| Nhãn Critical (`y=1`) | 1.183 |
| Tỷ lệ Critical | 11,92% |

Phân phối số phiếu nghiêm trọng:

| `serious_votes` | Số phân đoạn |
|---:|---:|
| 0 | 6.810 |
| 1 | 1.933 |
| 2 | 846 |
| 3 | 337 |

Tổng số phân đoạn có ít nhất hai phiếu nghiêm trọng là `846 + 337 = 1.183`, khớp chính xác với số nhãn dương. Tỷ lệ lớp dương 11,92% cho thấy dữ liệu mất cân bằng lớp; vì vậy accuracy đơn lẻ không đủ để đánh giá mô hình. Các chỉ số xếp hạng và phát hiện lớp dương như PR-AUC, Recall@20%, Precision@20% và Lift@20% phù hợp hơn với mục tiêu ưu tiên rà soát.

## 5. Kiểm tra tính nhất quán và trường hợp biên

- Mã pipeline tổng hợp annotation theo từng `rater` trước khi cộng phiếu, tránh việc một người chấm có nhiều span lỗi làm tăng giả tạo số phiếu.
- Script chẩn đoán `experiments/week10_priority2_3.py` tái xây dựng nhãn theo cùng quy tắc cốt lõi; kết quả được ghi nhận trùng với nhãn trong bảng mô hình.
- Tất cả 9.926 phân đoạn có đủ 3 người chấm; không có trường hợp thiếu người chấm trong bảng đầu ra đã kiểm tra.
- Một kiểm tra sơ bộ trước đó từng báo một phân đoạn chỉ có 2 người chấm (`Online-A.1574`, `sky.com.20669`, `doc_id=7`, `seg_id=1161`). Khi đọc lại TSV bằng đúng cấu hình parser của pipeline, phân đoạn này có 4 dòng annotation thuộc 3 người chấm (rater 1, 2 và 6). Do đó, phát hiện “2 người chấm” trước đó là sai khác do cấu hình đọc TSV của lần audit sơ bộ, không phải lỗi của pipeline. Phân đoạn có 0 phiếu nghiêm trọng và nhãn `y=0`.
- Không có bằng chứng từ các kết quả hiện có cho thấy một phân đoạn có nhãn dương do một người chấm đóng góp nhiều phiếu.

## 6. Diễn giải và giới hạn

Định nghĩa hiện tại là một operational definition (định nghĩa thao tác) phục vụ bài toán nghiên cứu, không phải khẳng định rằng mọi lỗi nghiêm trọng trong dịch thuật đều được bao phủ đầy đủ. Việc chỉ chọn `Major` thuộc `Accuracy/*` và `Non-translation!` là một lựa chọn phạm vi có chủ đích, phù hợp với mục tiêu phát hiện lỗi nghiêm trọng về nội dung. Tuy nhiên:

- Ngưỡng 2/3 có thể bỏ qua lỗi chỉ được một người chấm phát hiện; đây là đánh đổi để tăng độ đồng thuận của nhãn.
- Nhãn phụ thuộc vào hệ thống phân loại và mức độ nghiêm trọng do người chấm MQM gán.
- Cần mô tả rõ quy tắc này trong báo cáo cuối, tránh gọi chung mọi lỗi `Major` là Critical Error.
- Nên thực hiện phân tích độ nhạy ở ngưỡng 1/3 và 3/3 nếu thời gian cho phép; không thay đổi nhãn chính sau khi đã khóa thí nghiệm nếu không có lý do và phiên bản dữ liệu được ghi lại.

## 7. Kết luận có thể sử dụng trong Final Report

Nhãn Critical Error được xây dựng ở cấp phân đoạn bằng cách tổng hợp chú giải MQM từ ba người chấm. Một phiếu nghiêm trọng được ghi nhận khi annotation có severity `Major` và thuộc nhóm `Accuracy/*` hoặc `Non-translation!`. Nhiều annotation của cùng một người chấm được gộp thành một phiếu nhị phân trước khi tổng hợp. Một phân đoạn được gán nhãn Critical khi có ít nhất hai trong ba người chấm xác nhận lỗi nghiêm trọng. Trên 9.926 phân đoạn MT, quy trình tạo ra 1.183 phân đoạn Critical (11,92%) và 8.743 phân đoạn non-Critical. Kiểm tra độc lập trên bảng đầu ra xác nhận mỗi phân đoạn có đủ ba người chấm, không có khóa phân đoạn trùng lặp và phân phối nhãn khớp với phân phối số phiếu. Vì vậy, nhãn được xem là nhất quán về mặt triển khai và có thể dùng cho các thí nghiệm tiếp theo, với điều kiện báo cáo nêu rõ đây là định nghĩa thao tác có ngưỡng đồng thuận 2/3.

## 8. Việc cần giữ lại để tái lập

- Mã pipeline: `src/build_model_dataset.py`
- Script đối chiếu: `experiments/week10_priority2_3.py`
- Bảng đầu ra: `results/week10/model_data/mt_segment_level_original_outputs.csv`
- Báo cáo này: `reports/label_definition_audit.md`

**Lưu ý:** Các con số trong báo cáo phản ánh kết quả đã được chạy và cung cấp trong nhật ký dự án. Báo cáo này không thay thế việc lưu script kiểm toán độc lập và stdout/log chạy script trong thư mục kết quả.
