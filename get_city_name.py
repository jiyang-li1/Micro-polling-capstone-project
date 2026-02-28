import pandas as pd
df = pd.read_excel('ZIP_Locale_Detail.xls')

df = df[['DELIVERY ZIPCODE','LOCALE NAME','PHYSICAL CITY','PHYSICAL STATE']]
df["DELIVERY ZIPCODE"] = df["DELIVERY ZIPCODE"].astype(str).str.zfill(5)
df.to_csv('ZIP_Locale_Detail.csv', index=False)