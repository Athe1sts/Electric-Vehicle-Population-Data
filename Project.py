import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math
import pyodbc
import warnings
import colorsys
import re
from mpl_toolkits.basemap import Basemap
from sqlalchemy import create_engine

# Read CSV file
file_path = r'C:\Users\admin\Downloads\Electric_Vehicle_Population_Data.csv'
data = pd.read_csv(file_path)

# Check for missing data
nan_summary = data.isna().sum().to_frame('number of NaN')
print(nan_summary)

# Data cleaning class definition
class CleanData:
    @staticmethod
    def clean_text(text):
        if pd.isna(text):
            return text
        return ' '.join(str(text).strip().split())
    
    @staticmethod
    def clean(data):
        data['Clean Alternative Fuel Vehicle (CAFV) Eligibility'] = data['Clean Alternative Fuel Vehicle (CAFV) Eligibility'].replace({
            'Not eligible due to low battery range': 'Not_Eligible',
            'Eligibility unknown as battery range has not been researched': 'Unverified',
            'Clean Alternative Fuel Vehicle Eligible': 'Eligible'
        })
        data = data.dropna(subset=['County', 'City'], how='all')
        data = data.drop(columns=['Postal Code', '2020 Census Tract', 'DOL Vehicle ID'])
        if 'Model Year' in data.columns:
            data['Model Year'] = pd.to_numeric(data['Model Year'], errors='coerce')
            data['Model Year'] = data['Model Year'].astype('Int64') 
        return data

    @staticmethod
    def fill_na_with_other_column(row, column, other_column, df):
        if pd.isna(row[column]):
            matching_values = df[df[other_column] == row[other_column]][column].dropna()
            if not matching_values.empty:
                return matching_values.iloc[0]
        return row[column]

# Clean the data FIRST
data = CleanData.clean(data)

# Check data after cleaning
print(f"Shape of data after cleaning: {data.shape}")
print("\nMissing values after cleaning:")
print(data.isna().sum())

# Define function to connect to SQL and upload CLEANED data
def connect_to_sql():
    try:
        engine = create_engine('mssql+pyodbc://YIN/Car?trusted_connection=yes&driver=SQL+Server', use_setinputsizes=False)
        
        # Write CLEANED DataFrame to SQL table
        data.to_sql(
            name='Electric_Car', 
            con=engine, 
            if_exists='replace',
            index=False
        )

        # Read data from SQL table to verify
        sql_data = pd.read_sql('SELECT * FROM Electric_Car', con=engine)
        print(sql_data.head())
        
    except Exception as e:
        print(f"Error: {e}")

# Connect to SQL and import CLEANED data
connect_to_sql()

# Analyst data

## Electric Vehicle Type 
vehicle_type_counts = data['Electric Vehicle Type'].value_counts()
plt.figure(figsize=(10, 8))
plt.pie(vehicle_type_counts.values, 
        labels=vehicle_type_counts.index,
        autopct='%1.1f%%',  
        shadow=True)
plt.title('Distribution of Electric Vehicle Type')
plt.axis('equal')
plt.legend(loc='best')
plt.show()

## Electric Vehicle Fuel
fuel_counts = data['Clean Alternative Fuel Vehicle (CAFV) Eligibility'].value_counts()
plt.figure(figsize=(10, 8))
plt.pie(fuel_counts.values, 
        labels=fuel_counts.index,
        autopct='%1.1f%%',  
        shadow=True)
plt.title('Distribution of Electric Vehicle Fuel Types')
plt.axis('equal')
plt.legend(loc='best')
plt.show()

## Electric Vehicle Range
plt.figure(figsize=(10, 6))
sns.boxplot(data=data, x='Electric Vehicle Type', y='Electric Range')
plt.title('Electric Range by Vehicle Type', pad=15, size=12)
plt.xlabel('Vehicle Type')
plt.ylabel('Electric Range (miles)')
plt.show()

## Model by Year 
plt.figure(figsize=(10, 6))
data['Model Year'].value_counts().sort_index().plot(kind='bar')
plt.title('Distribution of Vehicles by Model Year')
plt.xlabel('Model Year')
plt.ylabel('Count')
plt.show()

## Model by Year and Electric Type 
fig, ax = plt.subplots(figsize=(10, 6))
table_year_type.plot(kind='bar', stacked=True, colormap='RdYlGn', ax=ax)
plt.title('Model by Year and Electric Vehicle Type')
plt.xlabel('Model Year')
plt.ylabel('Count of VINs')
plt.legend(title='Electric Vehicle Type')
plt.show()

## Range by Manufacturer
plt.figure(figsize=(10, 6))
sns.boxplot(x='Make', y='Electric Range', data=data)
plt.title('Electric Range by Manufacturer')
plt.xlabel('Manufacturer')
plt.ylabel('Electric Range (miles)')
plt.xticks(rotation=90)
plt.show()

## Range of Vehicles over time
plt.figure(figsize=(10, 6))
plt.scatter(data['Model Year'], data['Electric Range'], alpha=0.1)
plt.title('Electric Range of Vehicles Over Time')
plt.xlabel('Model Year')
plt.ylabel('Electric Range (miles)')
plt.grid(True)
plt.show()

## Top 10 cities registration
top_cities = data['City'].value_counts().head(10)
plt.figure(figsize=(10, 6))
top_cities.plot(kind='bar')
plt.title('Top 10 Cities by Vehicle Registrations')
plt.xlabel('City')
plt.ylabel('Number of Registrations')
plt.xticks(rotation=45)
plt.show()

## Georaphical Distributions

# Vehicle Location
def extract_coordinates(location):
    match = re.match(r"POINT \(([-\d.]+) ([-\d.]+)\)", location)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

data['Vehicle Location'] = data['Vehicle Location'].astype(str)
data['Longitude'], data['Latitude'] = zip(*data['Vehicle Location'].map(extract_coordinates))
data = data.dropna(subset=['Longitude', 'Latitude'])

plt.figure(figsize=(10, 10))
m = Basemap(projection='merc', 
            llcrnrlat=45, urcrnrlat=50, 
            llcrnrlon=-125, urcrnrlon=-116, 
            resolution='i')

m.drawcoastlines()
m.drawstates()
m.drawcountries()
x, y = m(data['Longitude'].values, data['Latitude'].values)

m.scatter(x, y, s=10, c='red', marker='o', alpha=0.5)

plt.title("Electric Vehicle Locations in Washington State")
plt.show()