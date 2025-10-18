
# Проверим второй лист с топ компаниями
df_top = pd.read_excel(excel_file, sheet_name=1)
print("Топ компании:")
print(df_top.head(10))
print("\nКолонки:")
print(df_top.columns.tolist())
