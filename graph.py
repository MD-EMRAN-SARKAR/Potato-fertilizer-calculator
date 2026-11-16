from typing_extensions import dataclass_transform
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ১. কেমিক্যাল প্রসেসের একটি কাল্পনিক ডেটাসেট
data = {
    'Temperature_C': [25, 30, 35, 40, 45, 50],
    'Reaction_Time_min': [10, 15, 20, 25, 30, 35],
    'Yield_Percent': [85.5, 88.0, 92.3, 89.2, 94.0, 95.1],
    'Purity_Percent': [98.1, 97.5, 96.0, 95.2, 94.1, 92.0]
}

df_process = pd.DataFrame(data)
plt.figure(figsize=(7,8))
sns.heatmap(df_process.corr(), annot=True , cmap="coolwarm",fmt=".2f")
plt.title("PROCESS VARIABE CORRELATION HEATMAP",fontsize=12,fontweight="bold"
)
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# Seaborn দিয়ে Regression Plot (Trendline) তৈরি
plt.figure(figsize=(7, 5))
sns.regplot(
    x="Temperature_C",
    y="Purity_Percent",
    data=df_process,
    color="darkred",
    marker="s",
)

plt.title(
    "Temperature vs Purity Trend Analysis", fontsize=12, fontweight="bold"
)
plt.xlabel("Temperature (°C)")
plt.ylabel("Purity (%)")
plt.grid(True, linestyle="--", alpha=0.5)
plt.show()
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress

# ১. ল্যাবের টাইম (মিনিট) এবং কনসেন্ট্রেশন (mol/L) ডেটা
time = np.array([0, 5, 10, 15, 20, 25, 30]) # Time in minutes
conc = np.array([1.00, 0.82, 0.67, 0.55, 0.45, 0.37, 0.30]) # Concentration C_t

# ২. First-Order Reaction এর জন্য ln(C_t) হিসাব করা
ln_conc = np.log(conc)

# ৩. Linear Regression প্রয়োগ করে slope (k) এবং R-squared বের করা
slope, intercept, r_value, p_value, std_err = linregress(time, ln_conc)

rate_constant_k = -slope # First order: ln(C_t) = -k*t + ln(C_0)
r_squared = r_value**2

print(f"Rate Constant (k): {rate_constant_k:.4f} min^-1")
print(f"R-squared (R^2): {r_squared:.4f}")

# ৪. Kinetics Plot তৈরি
plt.figure(figsize=(7, 5))
plt.plot(time, ln_conc, 'ro', label='Experimental Data')
plt.plot(time, slope*time + intercept, 'b--', label=f'Fit Line (R²={r_squared:.3f})')
plt.title('First-Order Reaction Kinetics', fontsize=12, fontweight='bold')
plt.xlabel('Time (min)')
plt.ylabel('ln(Concentration)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.show()
