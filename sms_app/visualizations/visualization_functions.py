import matplotlib as plt
import numpy as np
from datetime import datetime

def expendature_progress(limit, current):

  """
  Note: Requires Matplotlib and Numpy
  Function: Uses a budget and spent value to visualize the amount spent in contrast to limit

  Ex. of use:
  expendature_progress(1000, 200)
  """
  total = (int(current)/int(limit))*100
  total_str = str(total) + "%"
  fig, ax = plt.subplots(figsize=(6, 6))
  wedgeprops = {'width':0.3, 'edgecolor':'black', 'linewidth':3}
  ax.pie([100-total,total], wedgeprops=wedgeprops, startangle=90, colors=['#5DADE2', '#515A5A'])
  plt.title('Expendature Progress', fontsize=24, loc='center')
  plt.text(0, 0, total_str, ha='center', va='center', fontsize=42)
  plt.savefig('/openai_playground/Visualizations/images/Matplotlib_budget_progress_chart.png')
  plt.show()

###################################################

def piechart_visualization(example_dict):
  """
  Note: Requires Numpy & Matplotlib
  Requires a dictionary with categories as the keys and costs as the values of the dictionary.
  Function: Creates a pie chart for visualizing expendature in each category

  Ex. of dictionary:

    classify = { 'Transportation': 700,
                'Food': 300,
                'Personal':  300,
                'Entertainemnt': 200}

    piechart_visualization(classify)
  """
  cost = list(example_dict.values())
  category = list(example_dict.keys())

  pieplt = np.array(cost)


  fig = plt.figure()
  fig.patch.set_facecolor('black')

  plt.rcParams['text.color'] = 'white'

  plt.pie(cost, autopct='%1.1f%%')
  p=plt.gcf()

  plt.title("Total Expendature", fontsize=20)
  p.legend(title = "Total Expendature:", labels=category, loc=4, facecolor="gray")
  plt.savefig('/openai_playground/Visualizations/images/Matplotlib_pie_chart.png')


##########################################################################

def time_graph_visualization(day_of_month, dictionaryOfMoneySpent):
  """
  Note: Requires matplotlib and datetime
  Function: Illustrates spending habits in a specified amount of time

  Ex of data required: (dictionary)

  money_spent_per_day = {"01-23-2022": 40, 
                  "01-15-2022": 98, 
                  "01-04-2022": 94, 
                  "01-18-2022": 87,
                  "01-12-2022": 100,
                  "01-06-2022": 19,
                  "01-26-2022": 56}

  #Key Column represents the day. Value Column represents the money spent
  #Note: All dates in dictionary must be in the same month
  time_graph_visualization(30, money_spent_per_day)
  """
  money_spent = list(dictionaryOfMoneySpent.keys())
  spent = list(dictionaryOfMoneySpent.values())
  total_expense = sum(dictionaryOfMoneySpent.values())

  day_list = []

  for s in money_spent:
    day_classifier = datetime.strptime(s, "%m-%d-%Y")
    day = day_classifier.day
    day_list.append(day)

  days = []
  for i in range(day_of_month + 1):
    days.append(i)
  days.remove(0)

  matching = list(set(day_list) & set(days))

  plt.clf()
  plt.title('\$' + str(total_expense) + " Spent In The Last Month", fontsize=23, color='blue')
  plt.plot(matching, spent, 'bo-')
  plt.savefig('/openai_playground/Visualizations/images/Matplotlib_save_plot.png')



