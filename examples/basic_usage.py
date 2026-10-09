from ragdefender.datasets import generate_synthetic_dataset
from ragdefender.defense import RAGDefender


def main() -> None:
    examples = generate_synthetic_dataset(seed=42, examples=4)
    sample = examples[0]
    defense = RAGDefender(top_k=3)
    result = defense.defend(sample.query, sample.documents, top_k=3)
    print(f"Query: {sample.query}")
    print(f"Kept documents ({len(result.kept_documents)}):")
    for document in result.kept_documents:
        print(" -", document)
    print(f"Removed summary ({len(result.removed_documents)}):")
    for document in result.removed_documents:
        print(" -", document)


if __name__ == "__main__":
    main()
