#!/usr/bin/env python3
import csv, json, re, unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
FOODS=ROOT/'data'/'foods.js'
VERIFIED_ON='2026-09-26'

FANCY_CATALOG='https://www.purina.com/fancy-feast/products/wet-cat-food'
FRISKIES_CATALOG='https://www.purina.com/friskies/products/wet-cat-food'

# Official Purina wet-food listing titles captured from the live catalog on 2026-09-26.
# The site is paginated and dynamic. We preserve the raw manufacturer listing title as raw_title,
# and derive a shorter current_name for in-app shelf-name display without changing source nutrition rows.
FANCY_RAW = [
# page 1
'Fancy Feast Kitten Tender Chicken Feast Paté Wet Kitten Food',
'Fancy Feast Kitten Tender Salmon Feast Paté Wet Kitten Food',
'Purina Fancy Feast Delights With Cheddar Grilled Whitefish & Cheddar Cheese Feast Cat Food',
'Purina Fancy Feast Gravy Lovers Beef Feast Gourmet Cat Food in Wet Cat Food Gravy',
'Purina Fancy Feast Gravy Lovers Chicken and Beef Feast Gourmet Cat Food in Wet Cat Food Gravy',
'Fancy Feast Classic Paté Tender Beef Feast Gourmet Wet Cat Food',
'Fancy Feast Grilled Tender Beef & Liver Feast In Gravy Gourmet Wet Cat Food',
'Fancy Feast Grilled Liver & Chicken Feast In Gravy Gourmet Wet Cat Food',
'Fancy Feast Savory Centers Paté With Beef and a Gourmet Gravy Center',
'Fancy Feast Grilled Chicken & Beef Feast In Gravy Gourmet Wet Cat Food',
# page 2
'Purina Fancy Feast Wet Cat Food Flaked Tuna Feast',
'Purina Fancy Feast Sliced Chicken Feast Wet Cat Food in Gravy',
'Purina Fancy Feast Sliced Chicken Hearts and Liver Feast Wet Cat Food',
'Fancy Feast Kitten Tender Ocean Whitefish Feast Paté Wet Kitten Food',
'Fancy Feast Kitten Tender Turkey Feast Paté Wet Kitten Food',
'Fancy Feast Grilled Turkey Feast In Gravy Gourmet Cat Food',
'Fancy Feast Grilled Chicken Feast In Gravy Gourmet Cat Food',
'Fancy Feast Grilled Ocean Whitefish & Tuna Feast In Gravy Gourmet Cat Food',
'Fancy Feast Grilled Salmon & Shrimp Feast In Gravy Gourmet Cat Food',
'Fancy Feast Classic Paté Salmon & Shrimp Feast Gourmet Wet Cat Food',
# page 3
'Purina Fancy Feast Chunky Chicken Feast Wet Cat Food',
'Purina Fancy Feast Wet Cat Food Flaked Fish and Shrimp Feast',
'Purina Fancy Feast Wet Cat Food Flaked Trout Feast',
'Fancy Feast Classic Paté Tender Chicken and Liver Feast Gourmet Wet Cat Food',
'Fancy Feast Classic Paté Chopped Grill Feast Gourmet Wet Cat Food',
'Fancy Feast Classic Paté Ocean Whitefish & Tuna Feast Gourmet Wet Cat Food',
'Fancy Feast Classic Paté Turkey & Giblets Feast Gourmet Wet Cat Food',
'Fancy Feast Grilled Salmon Feast In Gravy Gourmet Cat Food',
'Purina Fancy Feast Gravy Lovers Salmon Feast Gourmet Cat Food in Wet Cat Food Gravy',
'Fancy Feast Classic Paté Tender Beef & Chicken Feast Gourmet Wet Cat Food',
# page 4
'Purina Fancy Feast Wet Cat Food Flaked Chicken and Tuna Feast',
'Purina Fancy Feast Wet Cat Food Flaked Tuna and Mackerel Feast',
'Purina Fancy Feast Gravy Lovers Chicken Hearts and Liver Feast Gourmet Cat Food in Wet Cat Food Gravy',
'Fancy Feast Savory Centers Paté With Chicken and a Gourmet Gravy Center',
'Fancy Feast Savory Centers Paté With Tuna and a Gourmet Gravy Center',
'Fancy Feast Classic Paté Tender Beef & Liver Feast Gourmet Wet Cat Food',
'Fancy Feast Sliced Beef Gourmet Wet Cat Food in Gravy',
'Fancy Feast Minced Turkey Gourmet Wet Cat Food in Sauce',
'Fancy Feast Grilled Beef Feast In Gravy Gourmet Wet Cat Food',
'Fancy Feast Marinated Morsels Turkey Gourmet Wet Cat Food in Gravy',
# page 5
'Fancy Feast Marinated Morsels Tuna Gourmet Wet Cat Food in Gravy',
'Fancy Feast Marinated Morsels Salmon Gourmet Wet Cat Food in Gravy',
'Fancy Feast Marinated Morsels Chicken Gourmet Wet Cat Food in Gravy',
'Fancy Feast Marinated Morsels Beef Gourmet Wet Cat Food in Gravy',
'Purina Fancy Feast Delights With Cheddar Grilled Tuna & Cheddar Cheese Feast in Wet Cat Food Gravy Cat Food',
'Purina Fancy Feast Delights With Cheddar Grilled Chicken & Cheddar Cheese Feast in Wet Cat Food Gravy Cat Food',
'Purina Fancy Feast Delights With Cheddar Grilled Turkey & Cheddar Cheese Feast in Wet Cat Food Gravy Cat Food',
'Fancy Feast Classic Paté Seafood Collection Variety Pack Cat Food - 45 cans',
'Fancy Feast Savory Centers Paté With Salmon and a Gourmet Gravy Center',
'Purina Fancy Feast Gravy Lovers Salmon and Sole Feast Gourmet Cat Food in Wet Cat Food Gravy',
# page 6
'Purina Fancy Feast Gravy Lovers Turkey Feast Gourmet Cat Food in Wet Cat Food Gravy',
'Fancy Feast Grilled Seafood Feast In Gravy Gourmet Cat Food',
'Fancy Feast Classic Paté Chicken Feast Wet Cat Food Variety Pack – 24 Cans',
'Fancy Feast Gems Mousse Paté With Beef and a Halo of Savory Gravy Wet Cat Food',
'Fancy Feast Gems Mousse Paté With Chicken and a Halo of Savory Gravy Wet Cat Food',
'Fancy Feast Gems Mousse Paté With Salmon and a Halo of Savory Gravy Wet Cat Food',
'Fancy Feast Gems Exquisite Mousse Collection Variety Pack – 12 Dual Packs',
'Purina Fancy Feast Gravy Lovers Beef Feast Paté in Gravy Wet Cat Food',
'Purina Fancy Feast Gravy Lovers Chicken Feast Paté in Gravy Wet Cat Food',
'Purina Fancy Feast Gravy Lovers Ocean Whitefish & Tuna Feast Paté in Gravy Wet Cat Food',
# page 7
'Purina Fancy Feast Gravy Lovers Salmon Feast Paté in Gravy Wet Cat Food',
'Purina Fancy Feast Gravy Lovers Paté in Gravy Wet Cat Food Variety Pack - 24 Cans',
'Fancy Feast Classic Paté Chicken Feast Gourmet Wet Cat Food',
'Purina Fancy Feast Gravy Lovers Chicken Feast in Gravy Gourmet Cat Food',
'Purina Fancy Feast Gravy Lovers Ocean Whitefish and Tuna Feast Gourmet Cat Food in Wet Cat Food Gravy',
'Fancy Feast Gourmet Naturals Natural White Meat Chicken Recipe In Gravy Wet Cat Food',
'Fancy Feast Medleys Wild Salmon Primavera With Tomatoes, Carrots & Spinach in a Silky Broth',
'Fancy Feast Medleys Beef & Pork Milanese with Potatoes and Carrots in Savory Juices Wet Cat Food',
'Fancy Feast Medleys Beef Ragù with Tomatoes & Pasta in a Savory Sauce Wet Cat Food',
'Fancy Feast Sliced Turkey Feast Wet Cat Food in Gravy',
# page 8
'Fancy Feast Kitten Classic Paté Salmon, Ocean Whitefish, Turkey & Chicken Variety Pack Wet Kitten Food - 24 Cans',
'Fancy Feast Medleys Primavera Wet Cat Food Variety Pack - 24 Cans',
'Fancy Feast Medleys Wild Salmon Florentine with Spinach in a Light Broth Gourmet Wet Cat Food',
'Fancy Feast Medleys Turkey Florentine with Spinach in a Light Broth Gourmet Wet Cat Food',
'Fancy Feast Medleys Tuna Florentine with Spinach in a Light Broth Gourmet Wet Cat Food',
'Fancy Feast Medleys White Meat Chicken Florentine with Spinach in a Light Broth Gourmet Wet Cat Food',
'Fancy Feast Gourmet Naturals Natural Beef Recipe Wet Cat Food',
'Fancy Feast Gourmet Naturals Natural White Meat Chicken Recipe Wet Cat Food',
'Fancy Feast Gourmet Naturals Natural Trout & Tuna Recipe Wet Cat Food',
'Fancy Feast Gourmet Naturals Natural Beef Recipe In Gravy Wet Cat Food',
# page 9
'Fancy Feast Gourmet Naturals Natural Wild Alaskan Salmon & Shrimp Recipe In Gravy Wet Cat Food',
'Fancy Feast Gourmet Naturals Natural Whitefish Recipe Wet Cat Food',
'Fancy Feast Gourmet Naturals Natural White Meat Chicken & Beef Recipe Wet Cat Food',
'Fancy Feast Medleys White Meat Chicken Primavera With Tomatoes, Carrots & Spinach in a Silky Broth',
'Fancy Feast Medleys White Meat Chicken With Carrots & Spinach in a Demi-Glace',
'Fancy Feast Medleys White Meat Chicken Florentine Paté With Cheese & Spinach',
'Fancy Feast Medleys Wild Alaskan Salmon With Carrots & Spinach in a Creamy Velouté Sauce',
'Fancy Feast Medleys Tuna Tuscany With Long Grain Rice & Spinach in a Savory Sauce',
'Fancy Feast Medleys Ocean Whitefish With Carrots & Spinach in a Creamy Béchamel Sauce',
'Fancy Feast Medleys White Meat Chicken Primavera Paté With Tomatoes, Carrots & Spinach',
# page 10
'Fancy Feast Medleys White Meat Chicken Tuscany Wet Cat Food With Long Grain Rice & Spinach in a Savory Sauce',
'Fancy Feast Medleys Tender Turkey Tuscany With Long Grain Rice & Spinach in a Savory Sauce',
'Fancy Feast Classic Paté Seafood Feast Gourmet Wet Cat Food',
'Fancy Feast Grilled Tuna Feast In Gravy Gourmet Wet Cat Food',
'Fancy Feast Classic Paté Cod, Sole & Shrimp Gourmet Wet Cat Food',
'Fancy Feast Classic Paté Savory Salmon Gourmet Wet Cat Food',
'Fancy Feast Gourmet Naturals Natural Wild Alaskan Salmon Recipe Wet Kitten Food',
'Fancy Feast Gourmet Naturals Natural Wild Alaskan Salmon Recipe Wet Cat Food',
'Fancy Feast Medleys Florentine Wet Cat Food Variety Pack - 24 Cans',
'Fancy Feast Classic Paté Seafood Collection Wet Cat Food Variety Pack – 12 Cans',
# page 11
'Purina Fancy Feast Sliced Poultry Favorites in Wet Cat Food Gravy 24 Ct Variety Pack',
'Fancy Feast Medleys Poultry Collection Gourmet Wet Cat Food Variety Pack',
'Fancy Feast Medleys Taste of Italy Collection Wet Cat Food Variety Pack – 30 Cans',
'Fancy Feast Classic Paté Seafood Collection Wet Cat Food Variety Pack – 24 Cans',
'Fancy Feast Classic Paté Seafood Collection Wet Cat Food Variety Pack – 30 Cans',
'Fancy Feast Marinated Morsels Poultry & Beef Gourmet Wet Cat Food Variety Pack - 24 Cans',
'Fancy Feast Senior 7+ Paté Chicken Feast',
'Fancy Feast Senior 7+ Minced Chicken Feast In Gravy',
'Fancy Feast Senior 7+ Paté Beef Feast',
'Fancy Feast Senior 7+ Minced Tuna Feast In Gravy',
# page 12
'Fancy Feast Petites Seared Salmon Entrée With Spinach in Gravy Gourmet Wet Cat Food',
'Fancy Feast Petites Grilled Chicken Entrée With Rice In Gravy Gourmet Wet Cat Food',
'Fancy Feast Petites Ocean Whitefish Entrée With Tomato in Gravy Gourmet Wet Cat Food',
'Fancy Feast Petites Tender Beef Entrée with Carrots in Gravy Gourmet Wet Cat Food',
'Fancy Feast Petites Roasted Turkey Entrée with Sweet Potato in Gravy Gourmet Wet Cat Food',
'Fancy Feast Medleys Tuna Primavera With Tomatoes, Carrots & Spinach in a Silky Broth',
'Fancy Feast Medleys Tender Turkey Primavera With Tomatoes, Carrots & Spinach in a Silky Broth',
'Fancy Feast Medleys Shredded Wild Salmon Fare With Spinach in a Savory Broth Wet Cat Food',
'Fancy Feast Medleys Shredded White Meat Chicken Fare With Spinach in a Savory Broth Wet Cat Food',
'Fancy Feast Medleys Shredded Turkey Fare With Spinach in a Savory Broth Wet Cat Food',
# page 13
'Fancy Feast Medleys Shredded Tuna Fare With Spinach in a Savory Broth Wet Cat Food',
'Fancy Feast Medleys Tuscany Collection Variety Pack – 12 Cans',
'Fancy Feast Medleys Seafood Collection Wet Cat Food Variety Pack – 30 Cans',
'Fancy Feast Classic Paté Chicken Feast Wet Cat Food Variety Pack – 12 Cans',
'Fancy Feast Savory Centers Wet Cat Food with a Gourmet Gravy Center 12 Count Variety Pack - Chicken, Salmon, Beef, and Tuna Paté',
'Fancy Feast Kitten Classic Paté Ocean Whitefish & Turkey Collection Variety Pack Wet Kitten Food - 12 cans',
'Fancy Feast Chicken Gourmet Wet Cat Food Variety Pack - 24 Cans',
'Fancy Feast Senior Classic Chicken Paté, Beef Paté, Chicken In Gravy & Tuna In Gravy Variety Pack Wet Cat Food – 12 Cans',
'Fancy Feast Medleys Shredded Fare Wet Cat Food Variety Pack - 12 Cans',
'Fancy Feast Medleys Primavera Wet Cat Food Variety Pack – 12 Cans',
# page 14
'Fancy Feast Petites Single-Serve Wet Cat Food In Gravy Collection Variety 24 Pack',
'Fancy Feast Medleys Pork Barbacoa Recipe With Rice, Tomatoes & Carrots in Savory Juices Wet Cat Food',
'Fancy Feast Medleys Carne Asada Recipe With Potatoes & Carrots in Savory Juices Wet Cat Food',
'Purina Fancy Feast Gems Mousse Paté Salmon & Tuna Collection Topped With Savory Gravy Wet Cat Food Variety Pack',
'Fancy Feast Gems Mousse Paté Chicken & Beef Variety Pack Topped With Savory Gravy Wet Cat Food',
'Fancy Feast Petites Single-Serve Gravy Collection Variety Pack Wet Cat Food - 12 Packs',
]
FANCY_DISCONTINUED = {'Fancy Feast Medleys Florentine Wet Cat Food Variety Pack - 24 Cans'}

FRISKIES_RAW = [
# page 1
'Friskies Paté Salmon Dinner Wet Cat Food',
'Friskies Shreds Chicken & Salmon Dinner In Gravy Wet Cat Food',
'Friskies Prime Filets With Chicken in Gravy Wet Cat Food',
'Friskies Ocean Favorites Meaty Bits With Salmon, Shrimp & Brown Rice In Sauce Wet Cat Food',
'Friskies Wild Favorites Mini Bites With Wild Caught Cod & Kale In Sauce Wet Cat Food',
'Friskies Wild Favorites Mini Bites With Wild Caught Tuna & Sweet Potato In Sauce Wet Cat Food',
'Friskies Wild Favorites Mini Bites With Wild Caught Sardines & Kale In Sauce Wet Cat Food',
'Friskies Wild Favorites Mini Bites With Wild Caught Haddock & Sweet Potato In Sauce Wet Cat Food',
'Friskies Paté Chicken & Tuna Dinner Wet Cat Food',
'Friskies Paté Country Style Dinner Wet Cat Food',
# page 2
'Friskies Paté Turkey & Giblets Dinner Wet Cat Food',
'Friskies Paté Liver & Chicken Dinner Wet Cat Food',
"Friskies Paté Mariner's Catch Wet Cat Food",
'Friskies Paté Mixed Grill Wet Cat Food',
'Friskies Paté Ocean Whitefish & Tuna Dinner Wet Cat Food',
'Friskies Paté Poultry Platter Wet Cat Food',
"Friskies Paté Sea Captain's Choice Wet Cat Food",
'Friskies Meaty Bits With Beef in Gravy Wet Cat Food',
'Friskies Meaty Bits Chicken Dinner in Gravy Wet Cat Food',
'Friskies Meaty Bits Gourmet Grill in Gravy Wet Cat Food',
# page 3
'Friskies Farm Favorites Paté With Chicken & Carrots Wet Cat Food',
'Friskies Farm Favorites Paté With Salmon & Spinach Wet Cat Food',
'Friskies Farm Favorites Meaty Bits With Turkey & Carrots In Gravy Wet Cat Food',
'Friskies Farm Favorites Meaty Bits With Whitefish & Spinach In Gravy Wet Cat Food',
'Friskies Ocean Favorites Paté With Salmon, Brown Rice & Peas Wet Cat Food',
'Friskies Ocean Favorites Paté With Tuna, Brown Rice & Peas Wet Cat Food',
'Friskies Ocean Favorites Meaty Bits With Tuna, Crab & Brown Rice In Sauce Wet Cat Food',
'Friskies Prime Filets With Beef in Gravy Wet Cat Food',
'Friskies Prime Filets Chicken & Tuna Dinner in Gravy Wet Cat Food',
'Friskies Prime Filets With Ocean Whitefish & Tuna in Sauce Wet Cat Food',
# page 4
'Friskies Prime Filets With Salmon & Beef in Sauce Wet Cat Food',
'Friskies Prime Filets Turkey Dinner in Gravy Wet Cat Food',
'Friskies Shreds With Chicken In Gravy Wet Cat Food',
'Friskies Shreds With Ocean Whitefish & Tuna In Sauce Wet Cat Food',
'Friskies Shreds With Whitefish & Sardines In Sauce Wet Cat Food',
'Friskies Shreds With Salmon In Sauce Wet Cat Food',
'Friskies Shreds Turkey & Cheese Dinner In Gravy Wet Cat Food',
'Friskies Shreds With Turkey & Giblets In Gravy Wet Cat Food',
'Friskies Shreds With Beef In Gravy Wet Cat Food',
'Friskies Gravy Sensations With Ocean Whitefish & Tuna In Gravy Wet Cat Food',
# page 5
'Purina Friskies Wet Cat Food Tasty Treasures With Chicken in Gravy (With Liver)',
'Purina Friskies Wet Cat Food Tasty Treasures With Ocean Fish and Tuna in Sauce (Scallop Flavor)',
'Purina Friskies Wet Cat Food Tasty Treasures With Chicken and Tuna in Gravy (Scallop Flavor)',
'Purina Friskies Wet Cat Food Tasty Treasures With Turkey and Liver in Gravy',
'Purina Friskies Indoor Cat Food Pate Chicken Dinner With Garden Greens',
'Purina Friskies Indoor Cat Food Chunky Chicken and Turkey Casserole With Garden Greens in Gravy 24/5.5 oz',
'Purina Friskies Indoor Cat Food Flaked Ocean Whitefish Dinner With Garden Greens in Sauce',
'Purina Friskies Indoor Cat Food Meaty Bits Homestyle Turkey Dinner With Garden Greens in Gravy',
'Purina Friskies Indoor Cat Food Meaty Bits Saucy Seafood Bake With Garden Greens in Sauce',
'Purina Friskies Extra Gravy Wet Cat Food Chunky With Beef in Savory Gravy',
# page 6
'Purina Friskies Extra Gravy Wet Cat Food Chunky Chicken in Savory Gravy',
'Purina Friskies Extra Gravy Wet Cat Food Chunky With Salmon in Savory Gravy',
'Purina Friskies Extra Gravy Wet Cat Food Chunky With Turkey in Savory Gravy',
'Friskies Extra Gravy Paté With Chicken In Savory Gravy Wet Cat Food',
'Friskies Extra Gravy Paté With Salmon In Savory Gravy Wet Cat Food',
'Friskies Extra Gravy Paté With Tuna In Savory Gravy Wet Cat Food',
'Friskies Extra Gravy Paté With Turkey In Savory Gravy Wet Cat Food',
'Friskies Paté Wet Cat Food 24 Ct Variety Pack',
'Friskies Paté Wet Cat Food 12 Ct Variety Pack',
"Friskies Surfin' & Turfin' Paté Favorites Wet Cat Food 32 Ct Variety Pack",
# page 7
'Friskies Shreds Chicken Lovers Prime Filets & Shreds Wet Cat Food 32 Ct Variety Pack',
'Purina Friskies Fish a Licious Wet Cat Food 32ct Variety Pack',
'Friskies Poultry Wet Cat Food 32 Ct Variety Pack with No Artificial Preservatives',
'Friskies Poultry Paté Favorites Wet Cat Food 32 Ct Variety Pack',
'Friskies Seafood Paté Favorites Wet Cat Food 32 Ct Variety Pack',
'Friskies Seafood & Chicken Paté Favorites Wet Cat Food 40 Ct Variety Pack',
"Friskies Surfin’ & Turfin’ Prime Filets Favorites Wet Cat Food 40 Ct Variety Pack",
'Purina Friskies Wet Cat Food 40 ct Variety Pack, Oceans of Delight Flaked and Prime Filets',
'Purina Friskies Wet Cat Food Gravy 40ct Variety Pack, TurChicken Extra Gravy Chunky, Meaty Bits and Prime Filets',
'Friskies Ocean Favorites Wet Cat Food 24 Ct Variety Pack',
# page 8
'Friskies Farm Favorites Paté Wet Cat Food 24 Ct Variety Pack',
'Friskies Meaty Bits Wet Cat Food 24 Ct Variety Pack',
'Friskies Meaty Bits Wet Cat Food 12 Ct Variety Pack',
'Friskies Pate Variety Pack 60 Count Wet Cat Food',
'Friskies Paté Wet Cat Food 48 Ct Variety Pack',
'Friskies Prime Filets Wet Cat Food 48 Ct Variety Pack',
'Friskies Shreds Wet Cat Food 24 Ct Variety Pack',
'Friskies Shreds Wet Cat Food 32 Ct Variety Pack',
'Friskies Shreds Wet Cat Food 40 Ct Variety Pack',
'Friskies Tasty Treasures Prime Filets Wet Cat Food 12 Ct Variety Pack',
# page 9
'Friskies Meaty Prime Filets Favorites Wet Cat Food 24 Ct Variety Pack',
'Friskies Tasty Treasures Prime Filets Wet Cat Food 24 Ct Variety Pack',
'Purina Friskies Indoor Cat Food 24ct VP - (Chicken and Turkey Casserole, Saucy Seafood Bake, Homestyle Turkey Dinner)',
'Purina Friskies Extra Gravy Wet Cat Food Chunky 24ct Variety Pack (With Chicken, Turkey, Salmon, Beef)',
'Friskies Seafood Prime Filets Favorites Wet Cat Food 24 Ct Variety Pack',
"Purina Friskies Surfin’ & Turfin’ Prime Filets Favorites Wet Cat Food 48 Ct Variety Pack",
'Purina Friskies TurChicken Meaty Bits Extra Gravy Wet Cat Food Variety Pack 48 Ct',
'Purina Friskies Wet Cat Food Variety Pack, Shreds With Beef, Turkey and Cheese Dinner, Chicken and Salmon Dinner, and With Ocean Whitefish and Tuna',
'Purina Friskies Paté Wet Cat Food Variety Pack Seafood and Chicken Paté Favorites 48ct VP',
'Purina Friskies Wet Cat Food Variety Pack, Oceans of Delight Flaked and Prime Filets',
# page 10
'Friskies Fully Load’d Chicken, Carrots, Tomatoes & Spinach in Gravy Wet Cat Food',
'Friskies Fully Load’d Salmon, Wild Rice, Carrots & Spinach in Sauce Wet Cat Food',
'Friskies Fully Load’d Tuna, Rice, Spinach & Tomatoes in Sauce Wet Cat Food',
'Friskies Fully Load’d Wet Cat Food 12 Count Variety Pack With Chicken, Salmon, or Tuna',
'Friskies Glaz’d & Infuz’d With Gravy Glaz’d Chicken Wet Cat Food',
'Friskies Glaz’d & Infuz’d With Gravy Glaz’d Crab Wet Cat Food',
'Friskies Glaz’d & Infuz’d With Gravy Glaz’d Shrimp Wet Cat Food',
'Friskies Glaz’d & Infuz’d Wet Cat Food 12 Count Variety Pack With Chicken, Crab or Shrimp',
'Friskies Meaty Bits Chicken Dinner in Gravy Wet Cat Food - 13.5oz',
'Friskies Meaty Bits With Ocean Fish in Sauce Wet Cat Food - 13.5oz',
# page 11
'Friskies Meaty Bits With Ocean Fish in Sauce & Chicken Dinner in Gravy Wet Cat Food 12ct Variety Pack',
"Friskies Lil' Soups Cat Food Complement 18 Ct Variety Pack",
]


def ascii_norm(s):
    return unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode()

def slug(s):
    s=ascii_norm(s).lower().replace('&',' and ')
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')[:96]

def clean_title(raw, brand):
    s=raw.replace('®','').replace('™','').replace(' ',' ').replace('–','-')
    s=re.sub(r'^Purina\s+','',s,flags=re.I)
    s=re.sub(r'^'+re.escape(brand)+r'\s+','',s,flags=re.I)
    # Keep meaningful texture/gravy wording but remove generic category-tail wording.
    s=re.sub(r'\s+Gourmet\s+Wet\s+Cat\s+Food\b','',s,flags=re.I)
    s=re.sub(r'\s+Wet\s+Kitten\s+Food\b','',s,flags=re.I)
    s=re.sub(r'\s+Wet\s+Cat\s+Food\b','',s,flags=re.I)
    s=re.sub(r'\s+Gourmet\s+Cat\s+Food\b','',s,flags=re.I)
    s=re.sub(r'\s+Cat\s+Food\b','',s,flags=re.I)
    s=re.sub(r'\s+with No Artificial Preservatives\b','',s,flags=re.I)
    s=re.sub(r'^Wet\s+','',s,flags=re.I)
    return re.sub(r'\s+',' ',s).strip(' -')

def fancy_line(name):
    n=name.lower()
    if 'gems' in n: return 'Gems'
    if 'petites' in n: return 'Petites'
    if 'gourmet naturals' in n: return 'Gourmet Naturals'
    if 'medleys' in n or any(x in n for x in ['tuscany','florentine','primavera','milanese','ragù','ragu','barbacoa','carne asada','demi-glace','velouté','bechamel','béchamel']): return 'Medleys'
    if 'senior 7+' in n or 'senior classic' in n: return 'Senior 7+'
    if 'kitten' in n: return 'Kitten'
    if 'savory centers' in n: return 'Savory Centers'
    if 'delights with cheddar' in n: return 'Delights With Cheddar'
    if 'gravy lovers' in n and 'paté in gravy' in n: return 'Gravy Lovers Paté in Gravy'
    if 'gravy lovers' in n: return 'Gravy Lovers'
    if 'classic paté' in n or 'classic pate' in n: return 'Classic Paté'
    if 'marinated morsels' in n: return 'Marinated Morsels'
    if 'grilled' in n: return 'Grilled'
    if 'flaked' in n: return 'Flaked'
    if 'sliced' in n: return 'Sliced'
    if 'minced' in n: return 'Minced'
    if 'chunky' in n: return 'Chunky'
    return 'Other'

def friskies_line(name):
    n=name.lower()
    if "lil' soups" in n or 'lil’ soups' in n: return "Lil' Soups"
    if 'fully load' in n: return "Fully Load'd"
    if 'glaz' in n and 'infuz' in n: return "Glaz'd & Infuz'd"
    if 'wild favorites' in n: return 'Wild Favorites Mini Bites'
    if 'farm favorites' in n: return 'Farm Favorites'
    if 'ocean favorites' in n: return 'Ocean Favorites'
    if 'tasty treasures' in n: return 'Tasty Treasures'
    if 'extra gravy' in n: return 'Extra Gravy'
    if 'gravy sensations' in n: return 'Gravy Sensations'
    if 'indoor' in n: return 'Indoor'
    if 'prime filets' in n: return 'Prime Filets'
    if 'shreds' in n: return 'Shreds'
    if 'meaty bits' in n: return 'Meaty Bits'
    if 'paté' in n or 'pate' in n: return 'Paté'
    return 'Variety Pack' if 'variety pack' in n else 'Other'

def family(name):
    n=name.lower()
    if 'variety pack' in n or 'collection' in n and any(x in n for x in [' cans',' pack',' dual']): return 'Variety Pack'
    if 'mousse' in n: return 'Mousse'
    if 'paté' in n or 'pate' in n: return 'Pâté'
    if 'shreds' in n: return 'Shreds'
    if 'prime filets' in n: return 'Filets'
    if 'meaty bits' in n or 'mini bites' in n: return 'Bites'
    if 'flaked' in n: return 'Flaked'
    if 'sliced' in n: return 'Sliced'
    if 'minced' in n: return 'Minced'
    if 'chunky' in n: return 'Chunky'
    if 'morsels' in n: return 'Morsels'
    if 'grilled' in n: return 'Grilled'
    if 'gravy' in n: return 'Gravy'
    if 'sauce' in n: return 'Sauce'
    return 'Wet Food'

def make_products(raws, brand, catalog, linefn, discontinued=frozenset()):
    products=[]; seen=set()
    for page_idx,raw in enumerate(raws,1):
        # page_idx here is order, not Purina page number; exact manufacturer catalog is still retained as source.
        if raw in seen: continue
        seen.add(raw)
        nm=clean_title(raw,brand)
        ln=linefn(nm)
        role='variety_pack' if ('variety pack' in raw.lower() or re.search(r'\b\d+\s*(?:ct|count|cans|pack|dual packs)\b',raw,re.I)) else 'complete_meal'
        if brand=='Friskies' and ("Lil' Soups" in raw or 'Lil’ Soups' in raw): role='complement'
        status='discontinued' if raw in discontinued else 'current'
        products.append({'brand':brand,'line':ln,'family':family(nm),'current_name':nm,'raw_title':raw,'role':role,'catalog_status':status,'manufacturer_category_url':catalog,'verified_on':VERIFIED_ON,'aliases':[]})
    used={}
    for p in products:
        base=('fancy' if brand=='Fancy Feast' else 'friskies')+'-'+slug(p['line'])+'-'+slug(p['current_name'])
        used[base]=used.get(base,0)+1
        p['id']=base if used[base]==1 else f'{base}-{used[base]}'
    return products


def load_foods():
    txt=FOODS.read_text(encoding='utf-8')
    m=re.search(r'window\.CATFOOD_DATA\s*=\s*(\[.*?\]);\s*window\.CATFOOD_META',txt,re.S)
    return json.loads(m.group(1))

STOP=set('wet cat food gourmet feast dinner recipe entree with in and the a an of natural tender savory'.split())
def norm(s):
    s=ascii_norm(s).lower().replace('&',' and ').replace("'",'').replace('’','')
    s=re.sub(r'\b(purina|fancy feast|friskies|wet|cat|food|gourmet|feast|dinner|recipe|entree|with|in|the|a|an|of)\b',' ',s)
    s=re.sub(r'\b(pate|patee|paté)\b',' pate ',s)
    s=re.sub(r'[^a-z0-9]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def core_tokens(s):
    return [t for t in norm(s).split() if t and t not in STOP]

def similarity(source, product):
    a=' '.join(core_tokens((source.get('product') or '')+' '+(source.get('style') or '')))
    b=' '.join(core_tokens(product['current_name']))
    if not a or not b: return 0.0
    A=set(a.split()); B=set(b.split())
    jac=len(A&B)/max(1,len(A|B))
    cov=len(A&B)/max(1,len(A))
    seq=SequenceMatcher(None,a,b).ratio()
    return .45*cov+.35*jac+.20*seq

def exactish(source, product):
    a=core_tokens((source.get('product') or '')+' '+(source.get('style') or ''))
    b=core_tokens(product['current_name'])
    if not a: return False
    A=set(a); B=set(b)
    # Source tokens must all survive into current title; tolerate one generic source token.
    return len(A-B)==0 or (len(A)>=4 and len(A-B)<=1 and len(A&B)/len(A)>=0.8)

FANCY_LINE_MAP={
 'classic':['Classic Paté'], 'classic pate':['Classic Paté'],
 'grilled in gravy':['Grilled'], 'roasted/flaked/chunky':['Flaked','Chunky','Grilled'],
 'sliced in gravy':['Sliced'], 'sliced':['Sliced'], 'marinated morsels in gravy':['Marinated Morsels'],
 'gravy lovers':['Gravy Lovers','Gravy Lovers Paté in Gravy'],
 'natural':['Gourmet Naturals'], 'gourmet naturals':['Gourmet Naturals'],
 'medleys florentine':['Medleys'], 'medleys primavera':['Medleys'], 'medleys tuscany':['Medleys'], 'medleys shredded':['Medleys'], 'medleys in gravy or broth':['Medleys'],
 'delights with cheddar':['Delights With Cheddar'], 'petites':['Petites'], 'kitten':['Kitten'],
}
FRISKIES_LINE_MAP={
 'classic pates':['Paté'], 'pate':['Paté'], 'pate with extra gravy':['Extra Gravy'],
 'savory shreds':['Shreds'], 'prime fillets':['Prime Filets'], 'gravy sensations':['Gravy Sensations'],
 'indoor':['Indoor'], 'meaty bits':['Meaty Bits'], 'flaked':['Other','Prime Filets'],
 'tasty treasures w/ cheese':['Tasty Treasures'], 'tasty treasures w/ bacon':['Tasty Treasures'],
 'saucesations':['Other'], 'cat concoctions':['Other'],
}

# Explicit high-confidence equivalences where old source line wording differs from current catalog taxonomy.
FANCY_MANUAL={
 # Pierson Classic
 'p14r04':'Classic Paté Chicken Feast', 'p14r05':'Classic Paté Tender Chicken and Liver Feast', 'p14r06':'Classic Paté Turkey & Giblets Feast',
 'p14r07':'Classic Paté Chopped Grill Feast', 'p14r08':'Classic Paté Tender Beef Feast', 'p14r09':'Classic Paté Tender Beef & Liver Feast',
 'p14r10':'Classic Paté Tender Beef & Chicken Feast', 'p14r11':'Classic Paté Seafood Feast', 'p14r12':'Classic Paté Ocean Whitefish & Tuna Feast',
 'p14r13':'Classic Paté Salmon & Shrimp Feast', 'p14r14':'Classic Paté Savory Salmon', 'p14r15':'Classic Paté Cod, Sole & Shrimp',
 # obvious flaked/chunky/sliced
 'p14r20':'Flaked Chicken and Tuna Feast','p14r21':'Flaked Tuna Feast','p14r22':'Flaked Tuna and Mackerel Feast','p14r24':'Flaked Trout Feast',
}
FRISKIES_MANUAL={
 'p20r19':'Paté Turkey & Giblets Dinner','p20r20':'Paté Poultry Platter','p20r21':'Paté Liver & Chicken Dinner','p20r22':'Paté Mixed Grill',
 'p20r23':'Paté Country Style Dinner','p21r04':'Paté Chicken & Tuna Dinner','p21r06':"Paté Mariner's Catch",'p21r07':"Paté Sea Captain's Choice",
 'p21r08':'Paté Salmon Dinner','p21r09':'Paté Ocean Whitefish & Tuna Dinner',
 'p21r13':'Shreds Chicken & Salmon Dinner In Gravy','p21r14':'Shreds Turkey & Cheese Dinner In Gravy','p21r15':'Shreds With Beef In Gravy',
 'p21r16':'Shreds With Chicken In Gravy','p21r17':'Shreds With Ocean Whitefish & Tuna In Sauce','p21r18':'Shreds With Salmon In Sauce',
 'p21r19':'Shreds With Turkey & Giblets In Gravy','p21r20':'Shreds With Whitefish & Sardines In Sauce',
}

def find_manual(products, needle):
    n=norm(needle)
    ranked=sorted(((SequenceMatcher(None,n,norm(p['current_name'])).ratio(),p) for p in products), key=lambda x:x[0], reverse=True)
    if ranked and ranked[0][0]>=0.72: return ranked[0][1]
    # fallback token containment
    N=set(core_tokens(needle))
    c=[p for p in products if N and N.issubset(set(core_tokens(p['current_name'])))]
    return c[0] if len(c)==1 else None

def build_brand(brand, products, brand_test, line_map, manual, outfile_stem, sources_extra=None):
    foods=load_foods()
    source_records=[]
    for f in foods:
        if brand_test(str(f.get('brand') or '')):
            source_records.append({'source_id':f['id'],'dataset':f.get('dataset'),'brand':f.get('brand'),'line':f.get('line'),'product':f.get('product'),'style':f.get('style'),'source_page':f.get('source_page'),'updated':f.get('updated'),'fpuo':bool(f.get('source_personal_use_only'))})
    links=[]
    for src in source_records:
        sid=src['source_id']
        if sid in manual:
            p=find_manual(products,manual[sid])
            if p:
                links.append({'source_id':sid,'current_product_id':p['id'],'status':'verified_name_match','confidence':1.0,'basis':'manual reconciliation against current official Purina catalog'})
                continue
        src_line=str(src.get('line') or '').lower()
        allowed=line_map.get(src_line)
        cands=[p for p in products if p['role']=='complete_meal' and p['catalog_status']=='current' and (not allowed or p['line'] in allowed)]
        ranked=sorted(((similarity(src,p),p) for p in cands), key=lambda x:x[0], reverse=True)
        if ranked:
            sc,p=ranked[0]
            second=ranked[1][0] if len(ranked)>1 else 0
            # Exactish names + line compatibility are safe enough to expose as verified aliases.
            blocked_auto = (brand=='Friskies' and src_line in {'tasty treasures w/ bacon','tasty treasures w/ cheese','saucesations','cat concoctions'}) or (brand=='Fancy Feast' and src_line=='natural')
            if (not blocked_auto) and exactish(src,p) and sc>=0.68 and sc-second>=0.035:
                links.append({'source_id':sid,'current_product_id':p['id'],'status':'verified_name_match','confidence':round(sc,3),'basis':'source recipe tokens match current official catalog entry within compatible product line'})
            elif sc>=0.82 and sc-second>=0.08:
                links.append({'source_id':sid,'current_product_id':p['id'],'status':'probable_name_match','confidence':round(sc,3),'basis':'normalized product-name similarity; retained as non-destructive reconciliation'})
            else:
                links.append({'source_id':sid,'current_product_id':None,'status':'unresolved','confidence':round(sc,3),'basis':'no sufficiently strong unambiguous current-catalog match'})
        else:
            links.append({'source_id':sid,'current_product_id':None,'status':'unresolved','confidence':0.0,'basis':'no compatible current-catalog candidate'})
    prod_by_id={p['id']:p for p in products}; src_by_id={s['source_id']:s for s in source_records}
    for l in links:
        if not l.get('current_product_id') or not str(l.get('status','')).startswith('verified_'): continue
        src=src_by_id[l['source_id']]; p=prod_by_id[l['current_product_id']]
        legacy=' · '.join(str(x) for x in [src.get('line'),src.get('product'),src.get('style')] if x)
        if legacy and legacy not in p['aliases']: p['aliases'].append(legacy)
    status_counts=Counter(l['status'] for l in links); line_counts=Counter(p['line'] for p in products); role_counts=Counter(p['role'] for p in products)
    obj={
      'meta':{
        'database':f'{brand} reconciliation database','schema_version':'1.0','verified_on':VERIFIED_ON,
        'scope':f'{brand} official wet-food catalog snapshot plus non-destructive links to existing CatFood Compass source records',
        'source_of_current_catalog':'Purina official website','current_catalog_url':products[0]['manufacturer_category_url'] if products else None,
        'preservation_rule':'Existing Pierson/FDSG records remain immutable source observations. This database links to them; it does not overwrite them.',
        'current_listing_count':sum(1 for p in products if p['catalog_status']=='current'),
        'catalog_entry_count':len(products),'source_record_count':len(source_records),'reconciliation_counts':dict(status_counts),
        'current_line_counts':dict(sorted(line_counts.items())),'role_counts':dict(role_counts),
        'notes':['Current manufacturer catalog names are stored separately from historical/source names.','A missing current match means unresolved, not discontinued, unless separately verified.','Only verified links are exposed to the app as current-name aliases.','The Purina product catalog is dynamic; this is a dated snapshot rather than a guarantee that a SKU remains on shelf.']
      },
      'sources':{'catalog':products[0]['manufacturer_category_url'] if products else None, **(sources_extra or {})},
      'current_products':products,'source_records':source_records,'reconciliation':links
    }
    jp=ROOT/'data'/f'{outfile_stem}.json'; jsp=ROOT/'data'/f'{outfile_stem}.js'; cp=ROOT/'data'/f'{outfile_stem}_reconciliation.csv'
    jp.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    var='FANCY_FEAST_DB' if brand=='Fancy Feast' else 'FRISKIES_DB'
    jsp.write_text(f'window.{var} = '+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    with cp.open('w',newline='',encoding='utf-8') as fh:
        w=csv.writer(fh); w.writerow(['source_id','dataset','source_brand','source_line','source_product','source_style','status','confidence','current_product_id','current_line','current_family','current_name','catalog_status','basis'])
        for l in links:
            s=src_by_id[l['source_id']]; p=prod_by_id.get(l.get('current_product_id'))
            w.writerow([s['source_id'],s.get('dataset'),s.get('brand'),s.get('line'),s.get('product'),s.get('style'),l.get('status'),l.get('confidence'),l.get('current_product_id'),p.get('line') if p else '',p.get('family') if p else '',p.get('current_name') if p else '',p.get('catalog_status') if p else '',l.get('basis')])
    return obj

fancy_products=make_products(FANCY_RAW,'Fancy Feast',FANCY_CATALOG,fancy_line,FANCY_DISCONTINUED)
friskies_products=make_products(FRISKIES_RAW,'Friskies',FRISKIES_CATALOG,friskies_line)

fancy=build_brand('Fancy Feast',fancy_products,lambda b:'fancy feast' in b.lower(),FANCY_LINE_MAP,FANCY_MANUAL,'fancy_feast',{
 'all_products':'https://www.purina.com/fancy-feast/products',
 'pate':'https://www.purina.com/fancy-feast/products/pate-wet-cat-food',
 'formula_update':'https://www.purina.com/fancy-feast/no-artificial-colors'
})
friskies=build_brand('Friskies',friskies_products,lambda b:'friskies' in b.lower(),FRISKIES_LINE_MAP,FRISKIES_MANUAL,'friskies',{
 'about':'https://www.purina.com/friskies/about',
 'faq':'https://www.purina.com/friskies/faq',
 'formula_rollout':'https://www.purina.com/friskies/no-artificial-colors-preservatives-wet-cat-food'
})

for obj in [fancy,friskies]:
    print(json.dumps(obj['meta'],indent=2,ensure_ascii=False))
    un=[x for x in obj['reconciliation'] if x['status']=='unresolved']
    print('Unresolved sample:',len(un),un[:5])
