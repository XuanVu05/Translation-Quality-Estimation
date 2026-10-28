# Translation Quality Estimation

## Project Structure

- `mqm_newstest2020_ende.tsv`: Source MQM dataset.
- `data/`: Official segment and document alignment mapping (`details/en-de.txt`).
- `original_outputs/`: Raw MT system translation outputs.
- `src/`: Core pipeline scripts (dataset building, document splitting, baseline training, test evaluation, and validation).
- `analysis/`: Data quality summary and MQM error analysis scripts.
- `experiments/`: Sensitivity analysis and system-identity model experiments.
- `results/week10/`: Week 10 experimental outputs and artifacts.

## Reproducibility

- Keep the original dataset unchanged.
- Preserve generated results, logs and configuration details.
- Run scripts from the project root unless their instructions specify otherwise.
- Paths in all scripts dynamically resolve relative to the project root directory.
