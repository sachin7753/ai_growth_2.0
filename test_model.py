"""Model validation: compare predictions against WHO growth standards."""
import torch, joblib, json, numpy as np

# Load model
class GrowthNet(torch.nn.Module):
    def __init__(self, n_layers=2, n_units=64, dropout_rate=0.3):
        super().__init__()
        layers = []
        in_features = 4
        for i in range(n_layers):
            layers.append(torch.nn.Linear(in_features, n_units))
            layers.append(torch.nn.ReLU())
            layers.append(torch.nn.Dropout(dropout_rate))
            in_features = n_units
        layers.append(torch.nn.Linear(in_features, 6))
        self.model = torch.nn.Sequential(*layers)
    def forward(self, x):
        return self.model(x)

with open("best_params.json") as f:
    params = json.load(f)
model = GrowthNet(params["n_layers"], params["n_units"], params["dropout_rate"])
model.load_state_dict(torch.load("growth_model.pth"))
model.eval()
scaler = joblib.load("scaler.joblib")

labels = {0: "Underweight", 1: "Healthy", 2: "Overweight", 3: "Obese", 4: "Stunted", 5: "Normal Ht"}

# Test cases: [age_months, height_cm, weight_kg, sex(1=M,0=F), expected_category]
# Based on WHO Child Growth Standards percentile tables
test_cases = [
    # --- HEALTHY children (WHO ~50th percentile height & weight) ---
    [12, 75.7, 9.6, 1, "Healthy/Normal"],     # 1yr boy
    [24, 87.1, 12.2, 1, "Healthy/Normal"],     # 2yr boy
    [36, 96.1, 14.3, 1, "Healthy/Normal"],     # 3yr boy
    [48, 103.3, 16.3, 1, "Healthy/Normal"],    # 4yr boy
    [12, 74.0, 8.9, 0, "Healthy/Normal"],      # 1yr girl
    [24, 86.4, 11.5, 0, "Healthy/Normal"],     # 2yr girl
    [36, 95.1, 13.9, 0, "Healthy/Normal"],     # 3yr girl

    # --- UNDERWEIGHT children (weight << P3 for age) ---
    [12, 75.7, 7.0, 1, "Underweight"],         # 1yr boy, very low wt
    [24, 87.1, 9.0, 1, "Underweight"],         # 2yr boy, very low wt
    [36, 96.1, 10.5, 1, "Underweight"],        # 3yr boy, very low wt
    [12, 74.0, 6.5, 0, "Underweight"],         # 1yr girl, very low wt

    # --- OVERWEIGHT / OBESE children (weight >> P97) ---
    [12, 75.7, 12.5, 1, "Overweight/Obese"],   # 1yr boy, high wt
    [24, 87.1, 16.5, 1, "Overweight/Obese"],   # 2yr boy, high wt
    [36, 96.1, 20.0, 1, "Overweight/Obese"],   # 3yr boy, very high wt
    [24, 86.4, 16.0, 0, "Overweight/Obese"],   # 2yr girl, high wt

    # --- STUNTED children (height << P3 for age) ---
    [24, 78.0, 10.5, 1, "Stunted"],            # 2yr boy, very short
    [36, 85.0, 12.5, 1, "Stunted"],            # 3yr boy, very short
    [48, 92.0, 13.0, 1, "Stunted"],            # 4yr boy, very short
    [24, 76.0, 10.0, 0, "Stunted"],            # 2yr girl, very short
]

header = "{:>5} {:>6} {:>6} {:>4} | {:>14} {:>6} | {:>16} | {:>5}".format(
    "Age", "Ht", "Wt", "Sex", "Predicted", "Conf", "Expected", "Match"
)
print(header)
print("-" * len(header))

correct = 0
total = len(test_cases)

for age, ht, wt, sex, expected in test_cases:
    inp = np.array([[age, ht, wt, sex]])
    inp_s = scaler.transform(inp)
    x = torch.tensor(inp_s, dtype=torch.float32)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        conf, pred_idx = torch.max(probs, dim=1)
    predicted = labels[int(pred_idx.item())]
    conf_pct = conf.item() * 100

    match = False
    if "Healthy" in expected and predicted in ["Healthy", "Normal Ht"]:
        match = True
    elif "Underweight" in expected and predicted == "Underweight":
        match = True
    elif "Overweight" in expected and predicted in ["Overweight", "Obese"]:
        match = True
    elif "Stunted" in expected and predicted == "Stunted":
        match = True

    if match:
        correct += 1
    s = "M" if sex == 1 else "F"
    mark = "OK" if match else "MISS"
    print("{:>5} {:>6.1f} {:>6.1f} {:>4} | {:>14} {:>5.1f}% | {:>16} | {:>5}".format(
        age, ht, wt, s, predicted, conf_pct, expected, mark
    ))

print("\n" + "=" * 60)
print("ACCURACY: {}/{} ({:.0f}%)".format(correct, total, correct / total * 100))
print("=" * 60)

# Show full probability distribution for key test cases
print("\n--- Detailed probability breakdown ---")
key_cases = [
    ("Healthy 2yr boy", [24, 87.1, 12.2, 1]),
    ("Underweight 2yr boy", [24, 87.1, 9.0, 1]),
    ("Overweight 3yr boy", [36, 96.1, 20.0, 1]),
    ("Stunted 3yr boy", [36, 85.0, 12.5, 1]),
]
for name, case in key_cases:
    inp = scaler.transform(np.array([case]))
    x = torch.tensor(inp, dtype=torch.float32)
    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)[0]
    print("\n  {}:".format(name))
    for i, p in enumerate(probs):
        bar = "#" * int(p.item() * 40)
        print("    {:>12}: {:5.1f}% {}".format(labels[i], p.item() * 100, bar))

# Model architecture summary
print("\n--- Model Architecture ---")
total_params = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print("  Layers: {}  |  Units: {}  |  Dropout: {:.2f}".format(
    params["n_layers"], params["n_units"], params["dropout_rate"]
))
print("  Total params: {:,}  |  Trainable: {:,}".format(total_params, trainable))
print("  Input features: 4 (age, height, weight, sex)")
print("  Output classes: 6 ({})".format(", ".join(labels.values())))
