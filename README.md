# Medicine-Sales-Analysis-Dashboard-with-Future-Business-Predictions

---

## 🧠 How It Works

1. **Data Ingestion:** The app reads `Mfg_Sales.csv` containing transaction-level data.
2. **Preprocessing:** 
   - Converts dates to `datetime` objects.
   - Maps months to **Financial Quarters** (e.g., April = Q1).
   - Generates **Financial Year** labels (e.g., `2024-25`).
3. **Visualization:** Uses `Plotly Express` to render interactive charts based on user selection (Bar, Line, Pie, Scatter, Area).

---

## 🔮 Future Roadmap

Based on the project analysis, here is the roadmap for upcoming features:

- [ ] **Forecasting Module:** Implement SARIMA/Prophet to predict next quarter's sales.
- [ ] **Database Integration:** Move from CSV to SQL/NoSQL for live data fetching.
- [ ] **PDF Export:** Allow users to download monthly business reports.
- [ ] **User Authentication:** Login system for Managers vs. Staff.

---

## 🤝 Contributing

Contributions are always welcome! 

1. **Fork** the project.
2. Create your **Feature Branch** (`git checkout -b feature/AmazingFeature`).
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`).
4. **Push** to the branch (`git push origin feature/AmazingFeature`).
5. Open a **Pull Request**.

---

<div align="center">
  
  **Built with ❤️ using Streamlit**
  
  [Report Bug](https://github.com/your-username/repo/issues) • [Request Feature](https://github.com/your-username/repo/issues)

</div>

