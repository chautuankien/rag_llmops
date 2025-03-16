from src.pipelines.feature_pipeline import feature_pipeline
from src.steps.feature_steps.data_extraction import extract_from_urls
from zenml import pipeline
from zenml.steps import step

# Setup pipeline
urls = ["https://docs.zenml.io/getting-started/installation"]
stats = feature_pipeline(urls)

print(f"Pipeline completed. Statistics: {stats}")

# sample_urls = [
#     "https://docs.zenml.io/getting-started/installation",
# ]

# results = extract_from_urls(sample_urls)
# print(f"Processed {len(results)} URLs successfully")

# @pipeline
# def pipeline():
#     sample_urls = [
#     "https://docs.zenml.io/getting-started/installation",
#     ]

#     results = extract_from_urls(sample_urls)
#     print(f"Processed {len(results)} URLs successfully")

# pipeline()



@step
def load_data() -> dict:
    """Simulates loading of training data and labels."""

    training_data = [[1, 2], [3, 4], [5, 6]]
    labels = [0, 1, 0]
    
    return {'features': training_data, 'labels': labels}

@step
def train_model(data: dict) -> None:
    """
    A mock 'training' process that also demonstrates using the input data.
    In a real-world scenario, this would be replaced with actual model fitting logic.
    """
    total_features = sum(map(sum, data['features']))
    total_labels = sum(data['labels'])
    
    print(f"Trained model using {len(data['features'])} data points. "
          f"Feature sum is {total_features}, label sum is {total_labels}")

@pipeline
def simple_ml_pipeline():
    """Define a pipeline that connects the steps."""
    dataset = load_data()
    train_model(dataset)

if __name__ == "__main__":
    run = simple_ml_pipeline()
    # You can now use the `run` object to see steps, outputs, etc.