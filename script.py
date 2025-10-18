
import pandas as pd

# Читаем Excel файл
excel_file = "Mosprom-2.xlsx"
xls = pd.ExcelFile(excel_file)

# Смотрим названия листов
print("Листы в файле:")
print(xls.sheet_names)
print("\n")

# Читаем первый лист
df = pd.read_excel(excel_file, sheet_name=0)
print("Структура данных:")
print(df.head(20))
print("\n")
print("Колонки:")
print(df.columns.tolist())
print("\n")
print("Типы данных:")
print(df.dtypes)
