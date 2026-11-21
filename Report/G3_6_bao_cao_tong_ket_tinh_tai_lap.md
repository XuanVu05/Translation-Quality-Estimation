# G3.6 – Báo cáo tổng kết tính tái lập

## 1. Mục đích

G3.6 tổng hợp các bằng chứng về khả năng tái lập của quy trình thực nghiệm cho bài toán phát hiện lỗi dịch thuật nghiêm trọng (Critical Error Detection – CED) trên bộ dữ liệu WMT 2020 MQM English–German.

Phạm vi kiểm chứng gồm: kiểm kê và truy xuất đầu vào; xác định môi trường thực thi; kiểm tra tính toàn vẹn của dữ liệu và locked split; tái tạo tập dữ liệu cấp đoạn; tái lập các thí nghiệm baseline, ablation và đánh giá cuối cùng trên Test.

Báo cáo phân biệt giữa kết quả đã được đối chiếu trực tiếp bằng dữ liệu/tệp đầu ra và những giới hạn chưa được kiểm chứng. Không xem việc chạy lại thành công trên cùng máy là bằng chứng tái lập độc lập trên một máy tính khác.

## 2. Tóm tắt kết quả

| Hạng mục | Bằng chứng và kết quả | Kết luận |
|---|---|---|
| G3.1 – Kiểm kê đầu vào và nguồn dữ liệu | Đã ghi nhận nguồn dữ liệu, tệp đầu vào, giấy phép ở cấp repository và SHA-256. Bảy tệp MT cùng tệp mapping được đối chiếu với archive WMT20 chính thức; 8/8 tệp khớp chính xác. | Đạt trong phạm vi các tệp đã kiểm tra |
| G3.2 – Môi trường thực thi | Python 3.13.18; pandas 3.1.0; NumPy 2.5.4; SciPy 1.18.1; scikit-learn 1.9.1. Môi trường sử dụng là `.venv_mla`; `requirements.txt` có SHA-256 `A6B946F0B69D5AB095FEB419E6F0EE1EBD6CD0FDCC45FC0D2568C665F54922F8`. | Đã ghi nhận và khóa phiên bản phụ thuộc |
| G3.4 – Toàn vẹn locked split | Source và snapshot có SHA-256 `780cd9f0b2b32042ad95f98e67318c03814fbe895e1f0ef8755da847e8d287ab`; dữ liệu, thứ tự dòng và cấu trúc khớp nhau. Strict verifier vượt qua 37/37 kiểm tra. | Đạt |
| G3.5.1 – Tái lập model dataset | Tập dữ liệu tái tạo có 9.926 dòng, 10 cột; dữ liệu và thứ tự dòng khớp bản gốc. SHA-256 của cả hai tệp là `90e3f978b20b511ea5c77e75469d85f3bb6b2573fae1cf8b428ac1cbe51d7530`. | Tái lập chính xác |
| G3.5.1 – Tái lập split | Tập split tái tạo khớp source locked split; SHA-256 của cả hai là `780cd9f0b2b32042ad95f98e67318c03814fbe895e1f0ef8755da847e8d287ab`. | Tái lập chính xác |
| G3.5.2 – Baseline | Đối chiếu 27 dòng metric giữa kết quả gốc và sandbox; tất cả giá trị trung bình, độ lệch chuẩn và sai khác đều khớp, sai khác bằng 0. | Tái lập chính xác |
| G3.5.3 – Ablation | Chạy lại ba cấu hình LR_Base, LR_Plus_System và System_Only trên Dev. Hai tệp CSV được cung cấp để đối chiếu có cùng SHA-256 và cùng nội dung. | Kết quả chạy lại được; đối chiếu tệp có giới hạn về truy xuất nguồn gốc |
| G3.5.4 – Test evaluation | Bốn tệp đầu ra gồm predictions, point metrics, metrics with CI và paired difference CI được đối chiếu; từng cặp có SHA-256 trùng khớp và nội dung giống nhau. | Tái lập chính xác các tệp kết quả đã đối chiếu |

## 3. Kiểm chứng dữ liệu và locked split

### 3.1. Tập dữ liệu cấp đoạn

Quy trình tạo model dataset được chạy lại trong sandbox `D:\\MLA_Reproduction_Test`. Kết quả gồm 9.926 đoạn dịch thuộc 7 hệ thống MT và 130 tài liệu. Mỗi hệ thống có 1.418 đoạn. Không có giá trị source/target bị thiếu; không có biến thể source trong cùng khóa đoạn.

Phân bố nhãn được tái tạo:

- Non-critical (`y=0`): 8.743 mẫu.
- Critical (`y=1`): 1.183 mẫu.
- Tỷ lệ Critical: xấp xỉ 11,918%.

Tệp model dataset gốc và tệp tái tạo có cùng kích thước cấu trúc `(9926, 10)`, cùng tên cột, cùng dữ liệu và cùng thứ tự dòng. SHA-256 của hai tệp đều là:

`90e3f978b20b511ea5c77e75469d85f3bb6b2573fae1cf8b428ac1cbe51d7530`

Đây là bằng chứng đối chiếu ở mức tệp, không chỉ là việc hai lần chạy cho ra cùng số lượng mẫu.

### 3.2. Locked split và kiểm tra rò rỉ theo document

Split được tổ chức theo document, không chia ngẫu nhiên từng segment độc lập. Phân bố đã khóa:

| Tập | Số mẫu | Số document | Số mẫu Critical |
|---|---:|---:|---:|
| Train | 6.797 | 90 | 803 |
| Dev | 1.554 | 20 | 218 |
| Test | 1.575 | 20 | 162 |
| Tổng | 9.926 | 130 | 1.183 |

Không có document overlap giữa Train, Dev và Test.

Tệp split tái tạo và snapshot gốc có cùng SHA-256:

`780cd9f0b2b32042ad95f98e67318c03814fbe895e1f0ef8755da847e8d287ab`

Strict verifier hiện tại kiểm tra sự tồn tại của các tệp, hash trong manifest, source–snapshot equality, cấu trúc và số lượng dữ liệu, khóa trùng lặp, nhãn nhị phân, document assignments, nội dung/thứ tự dòng của từng split, số lượng theo manifest và document overlap. Toàn bộ 37 kiểm tra đều đạt; chương trình kết thúc bằng:

`VERIFICATION PASSED: All checks passed.`

## 4. Tái lập thí nghiệm

### 4.1. Baseline trên Dev

Ba phương pháp được so sánh với random ranking: HeuristicRules, LogisticRegression và LinearSVM. Các metric được đối chiếu gồm PR-AUC, Recall@20%, Precision@20%, Lift@20% và MCC@20%.

| Phương pháp | PR-AUC | Recall@20% | Precision@20% | Lift@20% | MCC@20% |
|---|---:|---:|---:|---:|---:|
| Random | 0,143502 | 0,199633 | 0,139936 | 0,997523 | -0,000500 |
| HeuristicRules | 0,177704 | 0,330275 | 0,231511 | 1,650314 | 0,131399 |
| LogisticRegression | 0,196052 | 0,288991 | 0,202572 | 1,444025 | 0,089717 |
| LinearSVM | 0,174222 | 0,275229 | 0,192926 | 1,375262 | 0,075824 |

Đối chiếu trực tiếp 27 dòng metric giữa kết quả gốc và sandbox cho thấy mọi giá trị đều khớp; sai khác bằng 0. Random baseline trên Dev được tính trung bình qua 100 ranking với các seed 42–141.

### 4.2. Ablation trên Dev

Ba cấu hình được chạy lại:

- `LR_Base`: TF-IDF source/target và 12 đặc trưng bề mặt.
- `LR_Plus_System`: `LR_Base` bổ sung one-hot system.
- `System_Only`: chỉ sử dụng one-hot system.

| Metric | LR_Base | LR_Plus_System | System_Only |
|---|---:|---:|---:|
| PR-AUC | 0,196052 | 0,199116 | 0,156802 |
| Recall@20% | 0,288991 | 0,279817 | 0,252294 |
| Precision@20% | 0,202572 | 0,196141 | 0,176849 |
| Lift@20% | 1,444025 | 1,398183 | 1,260657 |
| MCC@20% | 0,089717 | 0,080455 | 0,052667 |
| Số mẫu Critical trong top 20% | 63 | 61 | 55 |

Kết quả cho thấy việc thêm metadata hệ thống làm PR-AUC tăng nhẹ nhưng làm giảm các metric ưu tiên vận hành tại top 20% so với `LR_Base`. `System_Only` thấp hơn `LR_Base` trên cả năm metric chính. Thí nghiệm này không chứng minh khả năng tổng quát hóa sang hệ thống MT chưa xuất hiện trong dữ liệu.

**Giới hạn đối chiếu:** hai tệp CSV ablation được cung cấp để so sánh có cùng SHA-256 `e22a76dbea1aa4d16ec298e8f6ee211d0045a1709c940fcc75d854e9da2349b8` và giống nhau về nội dung. Tuy nhiên, tên tệp tải lên không xác định rõ một tệp thuộc thư mục kết quả gốc và tệp còn lại thuộc sandbox. Vì vậy, bằng chứng xác nhận hai bản sao được cung cấp là giống nhau; không nên mô tả đây là đối chiếu có provenance đầy đủ giữa hai đường dẫn nguồn độc lập nếu chưa lưu lại bằng chứng đường dẫn.

### 4.3. Đánh giá cuối cùng trên Test

Mô hình được huấn luyện trên Train+Dev và đánh giá trên Test. Test gồm 1.575 mẫu thuộc 20 documents, trong đó có 162 mẫu Critical; tỷ lệ Critical là 10,286%. Ngân sách rà soát 20% tương ứng 315 mẫu.

| Phương pháp | PR-AUC | Recall@20% | Precision@20% | Lift@20% | MCC@20% |
|---|---:|---:|---:|---:|---:|
| Random | 0,1091 | 0,1975 | 0,1016 | 0,9877 | -0,0021 |
| HeuristicRules | 0,1391 | 0,3086 | 0,1587 | 1,5432 | 0,0920 |
| LogisticRegression | 0,1971 | 0,3148 | 0,1619 | 1,5741 | 0,0972 |
| LinearSVM | 0,1676 | 0,2346 | 0,1206 | 1,1728 | 0,0293 |

Logistic Regression xếp hạng tốt nhất theo PR-AUC và có 51 mẫu Critical trong top 315, so với 50 của heuristic. Tuy nhiên, bootstrap theo cụm document với 1.000 lần lặp cho thấy khoảng tin cậy của chênh lệch LR–heuristic ở Recall@20%, Precision@20%, Lift@20% và MCC@20% đều chứa 0. Chỉ chênh lệch PR-AUC có khoảng tin cậy không chứa 0: `+0,0580`, CI `[0,0151; 0,1232]`.

Do đó, kết quả hỗ trợ nhận định LR có PR-AUC tốt hơn heuristic trên Test trong thí nghiệm này; chưa đủ bằng chứng để kết luận LR vượt trội về hiệu quả ưu tiên rà soát trong ngân sách top 20%.

Bốn tệp đầu ra Test (`test_predictions.csv`, `test_point_metrics.csv`, `test_metrics_with_ci.csv`, `paired_difference_ci.csv`) được đối chiếu giữa bản gốc và sandbox. Mỗi cặp có SHA-256 trùng khớp và dữ liệu đọc vào giống nhau.

## 5. Môi trường và quy trình tái lập

Các lệnh chạy được thực hiện bằng interpreter:

`D:\\Translation-Quality-Estimation\\.venv_mla\\python.exe`

Phiên bản Python và các thư viện chính đã được ghi nhận trong báo cáo G3.4. Các script thực nghiệm cần thiết được sao chép vào sandbox và hash của bảy script được kiểm tra khớp với bản trong dự án gốc. Các tệp đầu vào gồm MQM, mapping và bảy tệp MT cũng được kiểm tra hash trước khi chạy.

Các giai đoạn tái lập được thực hiện trong thư mục sandbox riêng:

`D:\\MLA_Reproduction_Test`

Sandbox tách biệt thư mục kết quả khỏi dự án gốc, nhưng sử dụng cùng interpreter cài trên máy. Vì vậy, đây là kiểm chứng tái lập trong sandbox cùng máy, không phải kiểm chứng trên một hệ điều hành, máy tính hoặc cài đặt Python độc lập.

## 6. Giới hạn và rủi ro còn lại

1. **Chưa có tái lập liên máy:** chưa thực hiện cài đặt sạch trên máy tính thứ hai hoặc môi trường CI độc lập. Không khẳng định khả năng tái lập cross-machine.
2. **Giới hạn miền dữ liệu:** thí nghiệm sử dụng WMT 2020 English–German và bảy hệ thống MT. Chưa có bằng chứng tổng quát hóa sang ngôn ngữ, miền dữ liệu hoặc hệ thống MT khác.
3. **Số document Test hạn chế:** Test có 20 documents. Bootstrap theo document đã phản ánh cấu trúc phân cụm, nhưng số cụm vẫn còn hạn chế; cần thận trọng khi diễn giải khoảng tin cậy.
4. **Random baseline khác số lần lấy mẫu giữa Dev và Test:** Dev sử dụng trung bình 100 ranking; Test sử dụng một ranking với seed `20261026`. Khi so sánh random baseline giữa hai tập, cần nêu rõ khác biệt này.
5. **Ablation provenance:** hai CSV ablation được tải lên giống nhau theo hash, nhưng bằng chứng hiện có chưa xác định chắc chắn hai đường dẫn nguồn độc lập. Cần lưu lại phép đối chiếu có đường dẫn đầy đủ nếu muốn nâng mức xác nhận provenance.
6. **Giấy phép dữ liệu:** báo cáo audit ghi nhận giấy phép Apache 2.0 ở cấp repository. Điều này không tự động chứng minh mọi thành phần bên thứ ba hoặc archive WMT riêng biệt đều có quyền phân phối lại không giới hạn. Cần giữ nguyên cảnh báo này khi công bố dữ liệu hoặc mã nguồn.

## 7. Kết luận

Trong phạm vi môi trường đã kiểm tra, quy trình có bằng chứng tái lập mạnh ở các bước tạo model dataset, khóa split, chạy baseline và đánh giá Test. Model dataset và locked split được tái tạo khớp ở mức dữ liệu và SHA-256; baseline có 27 dòng metric khớp hoàn toàn; bốn tệp kết quả Test cũng khớp hash; strict verifier vượt qua 37/37 kiểm tra.

Ablation đã được chạy lại và các chỉ số được ghi nhận nhất quán với kết quả dự án; tuy nhiên, provenance của phép đối chiếu hai CSV ablation cần được mô tả thận trọng.

Kết luận phù hợp nhất là: **các kết quả thực nghiệm chính đã được tái lập trong sandbox trên cùng máy và cùng môi trường Python đã khóa; chưa chứng minh tái lập độc lập trên máy khác hoặc khả năng tổng quát hóa ngoài WMT 2020 English–German và bảy hệ thống MT được khảo sát.**

## 8. Danh mục bằng chứng liên quan

- `reports/dataset_license_audit.md`
- `reports/data_quality_audit.md`
- `reports/label_definition_audit.md`
- `reports/feature_provenance_audit.md`
- `reports/data_leakage_audit.md`
- `reports/G1_completion_summary.md`
- `reports/G2_experimental_evaluation_report.md`
- `reports/G3_4_reproducibility_environment_and_split_integrity.md`
- `reports/G3_5_2_bao_cao_tai_lap_baseline.md`
- `reports/G3_5_3_bao_cao_tai_lap_ablation.md`
- `reports/G3_5_4_bao_cao_tai_lap_test_evaluation.md`
- `src/verify_locked_split.py`
- `requirements.txt`
- `reports/source_file_manifest.csv`

---

**Ghi chú quản lý phiên bản:** báo cáo này tổng hợp các kết quả và bằng chứng đã được ghi nhận trong quá trình G3. Không thay thế các log gốc, manifest, tệp CSV đầu ra hoặc mã nguồn thực nghiệm. Khi nộp, cần giữ các tệp bằng chứng tương ứng trong repository và không đưa `.venv_mla/` hoặc tệp sao lưu verifier vào commit.
