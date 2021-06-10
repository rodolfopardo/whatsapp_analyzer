##Dependencies
import streamlit as st
import numpy as np
import pandas as pd
from os import path
from PIL import Image
import datetime
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import nltk
nltk.data.path.append('./nltk_data/')
from nltk.corpus import stopwords
from nltk import word_tokenize
import string
import re
import emoji
import regex
from datetime import datetime
import collections
stop_words_sp = stopwords.words('spanish')
stop_words_en = stopwords.words('english')
stop_words = stop_words_sp + stop_words_en + list(string.punctuation)

lista_palabras = ['haha', 'hehe', 'hihi', 'jaja', 'jjaa', 'jajj', 'ajja', 'juju', 'jaaj' 'jiji', 'jojo', 'ahhh', 'weee', 'guee', 'jeje', 'ayy', 'siii', 'nooo', ' uhhh', 'http']

import matplotlib.pyplot as plt
plt.style.use('seaborn-muted')
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

##App
st.set_page_config(page_title='Análisis WhatsApp', layout='wide')
st.title('Análisis Automático de Conversaciones de WhatsApp')
st.write('Creado por Lautaro Pacella')
with st.beta_expander("¿Cómo Funciona?", expanded = False):
    st.write("""
    Para comenzar, necesitas tener el archivo de tu conversación que brinda WhatsApp.\n
    Ingresá en la conversación que te gustaría analizar ->  "⁝"  -> "Más" -> "Exportar Chat"  -> "Sin archivos" -> esperar a que la aplicación produzca el archivo de la conversación.\n
    Por último, subir el archivo ¡y listo! vas a tener los datos de tu chat.
    """)

upload_file = st.file_uploader("WhatsApp Chat", accept_multiple_files = False, type = 'txt')
st.markdown('**El contenido de su conversación no será accesible para nadie ni será guardado.**')
if upload_file:
    with st.spinner('Analizando Conversación'):

        ##Get text data
        name_patt = re.compile(r'\-\s([a-zA-Z0–9áéíóúÁÉÍÓÚ]+\s?[a-zA-Z0–9áéíóúÁÉÍÓÚ]+\s?[a-zA-Z0–9áéíóúÁÉÍÓÚ]+\s?)\:\s')
        def get_date(text):
            try:
                date = datetime.strptime(text, '%d/%m/%y')
            except:
                date = datetime.strptime(text, '%d/%m/%Y')
            return date
        dates = []
        times = []
        authors = []
        messages = []

        for line in upload_file:
            try:
                date, time = str(line, 'utf-8').split()[0], str(line, 'utf-8').split()[1]
                author = name_patt.search(str(line, 'utf-8')).group(1)
                msg = ''.join(str(line, 'utf-8').split(':')[2:]).strip()
                dates.append(get_date(date))
                times.append(time)
                authors.append(author)
                messages.append(msg)
            except (IndexError, AttributeError) as error:
                continue  
        def split_count(text):
            emoji_list = []
            data = regex.findall(r'\X', text)
            for word in data:
                if any(char in emoji.UNICODE_EMOJI['es'] for char in word):
                    emoji_list.append(word)
            return emoji_list

        ##Building the DF
        df = pd.DataFrame({'Date': dates, 'Time': times, 'Author': authors, 'Content': messages})
        df.Date = pd.to_datetime(df.Date, errors='coerce')
        df.Time = df.Time + ':00'
        df.Time = pd.to_datetime(df.Time, errors='coerce')
        df.dropna(inplace=True)
        df = df.set_index('Time')
        df['Lenght']= df['Content'].str.split().str.len()
        df["emoji"] = df["Content"].apply(split_count)
        df['Year']= df['Date'].dt.year
        df['Month']= df['Date'].dt.month
        df['Day']= df['Date'].dt.day
        df['Week_of_Year'] = df['Date'].dt.isocalendar().week
        df['Day_of_Week'] = df['Date'].dt.dayofweek

        wc = df[df.Content != '<Multimedia omitido>']
        wc = wc[wc.Content != 'Este mensaje fue eliminado']

        def clean_string(string):
            pattern = re.compile(r'(\w+)')
            try:
                clean_string = pattern.search(string).group(1)
                a,b = 'áéíóúü','aeiouu'
                trans = str.maketrans(a,b)
                clean_string = clean_string.translate(trans)
            except AttributeError:
                clean_string = ""
            return clean_string

        def prepare_text(text):
           ## Tokenize and merge
            vocab = list()
            tmp = list()
            final = []
            tmp = text.split(' ')
           ## Normalize
            # To lowercase
            tmp = [word.lower() for word in tmp]
            # Remove punctuation and replace accented chars
            for w in tmp:
                cs = clean_string(w)
                if cs:
                    vocab.append(cs)
           ## Remove stopwords
            vocab = [w for w in vocab if w not in stop_words and w.isalpha()
                        and len(w)>3]
            words_re = re.compile("|".join(lista_palabras))
            for w in vocab:
                if words_re.search(w):
                    continue
                else:
                    final.append(w)
            return ' '.join(final)

        ### WORDCLOUD
        wc['Content'] = wc['Content'].apply(lambda x: prepare_text(x))
        wordcloud = WordCloud(background_color="black",stopwords=stop_words,
                              width = 1200, height = 500,
                             contour_color='black').generate(" ".join(wc['Content']))
        wc_plot = plt.figure(facecolor='black', figsize=(12,5), dpi = 500)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.title('Nube de las 200 Palabras más Utilizadas')
        plt.axis("off")
        plt.tight_layout(pad=0)

        ##Distribution of Messages during day Plot
        hours_count = pd.DataFrame({'Hours': df.resample(rule = 'H', origin=0).Content.count().index.astype('str'), 'Count': df.resample('1H', origin=0).Content.count().values})
        hours_count.Hours = hours_count.Hours.str.split(expand=True)[1].astype('str')
        hours_count['Hours'] = hours_count['Hours'].str[:-3]
        total_days =  df.Date.iloc[-1] -df.Date[0]
        hours_count['Normalized'] = hours_count.Count / total_days.days
        
        colors = ['lightslategray',] * 24
        colors[hours_count['Normalized'].argmax()] = 'crimson' 
        hours = go.Figure(data=[go.Bar(x = hours_count.Hours, y= hours_count.Normalized, marker_color = colors)])

        hours.update_layout(title = 'Cantidad Promedio de Mensajes por Horas del Día', 
                            xaxis_tickangle=-45, 
                            xaxis_title='', 
                            yaxis_title='Mensajes')


        ##Distribution of Messages per day of the week
        q_weeks = len(df.Week_of_Year.unique())
        days_count = pd.DataFrame({'Day': df.Day_of_Week.value_counts(sort=False).index,
                                   'Count': df.Day_of_Week.value_counts(sort=False).values, 
                                   'Normalized': df.Day_of_Week.value_counts(sort=False).values/q_weeks})
        colors = ['lightslategray',] * 7
        colors[days_count['Normalized'].argmax()] = 'crimson' 
        week = {0: 'Lunes', 1:'Martes', 2:'Miércoles', 3: 'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
        days_count.replace({'Day': week}, inplace=True)
        days_week = go.Figure(data=[go.Bar(x = days_count.Day, y = days_count.Normalized, marker_color = colors)])
        days_week.update_layout(title = 'Cantidad Promedio de Mensajes por Días de la Semana',
                                xaxis_title='', 
                                yaxis_title='Mensajes')
                
        
        ##Average of words per Msgs Plot
        lenght = df.groupby('Date')['Lenght'].mean()
        lenght_plot = go.Figure(data=go.Scatter(x=lenght.index, y=lenght.values,
                                                mode='markers'))
        lenght_plot.update_layout(yaxis_range=[-0,lenght.to_numpy().max()+2],
                    title = 'Promedio de Palabras por Mensajes', 
                    yaxis_title='Palabras')




        ##Average of Msgs per Author Plot
        msg_day_author = df.groupby(['Date', 'Author']).count().reset_index()
        msg_day_author_plot = go.Figure(data=px.scatter(msg_day_author, x = 'Date', y = 'Content',
                                                        color = 'Author',
                                                        title= 'Cantidad de Mensajes por Autor'))
        msg_day_author_plot.update_xaxes(title = '')
        msg_day_author_plot.update_yaxes(title = 'Mensajes')

        lenght_author = df.groupby(['Date', 'Author'])['Lenght'].mean()
        lenght_author = lenght_author.unstack().reset_index()


        ##Heatmap
        hm = df.groupby('Day_of_Week').resample('2h').Content.count().unstack(level=0).reset_index(drop=True)
        hm = hm.rename(columns={0: 'Lunes', 1:'Martes', 2:'Miércoles', 3: 'Jueves', 4:'Viernes', 
                                      5:'Sábado', 6:'Domingo'},
                             index={0: '00:00', 1:'02:00', 2:'04:00', 3:'06:00',4:'08:00',5:'10:00',
                                    6:'12:00', 7:'14:00', 8:'16:00', 9:'18:00', 10:'20:00', 11:'22:00', 12:'24:00'})
        hm.fillna(0, inplace=True)
        def df_to_plotly(df):
            return {'z': df.values.tolist(),
                    'x': df.columns.tolist(),
                    'y': df.index.tolist()}

        calendar = go.Figure(data=go.Heatmap(df_to_plotly(hm), colorscale ="Mint", colorbar=dict(
                tickvals=[hm.to_numpy().max()/30 * 2, hm.to_numpy().max()/30 * 28],
                ticktext=["Menos Mensajes", "Más Mensajes"],
                ticks="outside"
            )))
        calendar.update_layout(title = 'Promedio de mensajes por días de la semana en rangos de 2 hs',
                               title_xanchor= "left")
        
        ##Msgs per Author
        per_author = df.groupby('Author').size().sort_values(ascending=False)
        author = px.pie(values = per_author.values, names=per_author.index, 
                        title = 'Porcentaje de Mensajes por Autor',
                        color_discrete_sequence=px.colors.qualitative.Antique)
        author.update_traces(textposition='inside', textinfo='percent+label')




        ##Most used Emojis
        total_emojis_list = list([a for b in df.emoji for a in b])
        emoji_dict = dict(collections.Counter(total_emojis_list))
        emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)

        emoji_df = pd.DataFrame(emoji_dict[0:15], columns=['emoji', 'count'])



        ##Most used Emojis per Author
        authors = df.Author.unique()

        ##Data Description
        c_msgs = len(df)
        multimedia = len(df[df['Content'] == '<Multimedia omitido>'])
        eliminados = len(df[df['Content'] == 'Este mensaje fue eliminado'])
        duracion = df.Date[-1] - df.Date[0]
        with st.beta_expander("Datos Analizados de la Conversacion", expanded=True):
            mensaje1,mensaje2,mensaje3,rand,rand1,rand3 = st.beta_columns(6)
            with mensaje1:
                st.write(f'''
                Total de Mensajes: {c_msgs} \n ''')
            with mensaje2:
                st.write(f'''         
                Archivos Multimedia: {multimedia}\n ''')
            with mensaje3:
                st.write(f'''
                Mensajes Eliminados: {eliminados}\n ''')

            st.write(f'''Días Registrados: {duracion.days}\n''')
                     
            mensaje4,mensaje5,rand4,rand5,rand6,rand7 = st.beta_columns(6)
            with mensaje4:
                st.write(f'''
                Desde: {df.Date[0].day}/{df.Date[0].month}/{df.Date[0].year}\n ''')
            with mensaje5:
                st.write(f'''
                Hasta: {df.Date[-1].day}/{df.Date[-1].month}/{df.Date[-1].year}''')
        
        
        with st.beta_expander('Por autor'):
            col1,col2 = st.beta_columns(2)
            with col1:
                st.plotly_chart(author, use_container_width=True)
            with col2:
                st.write(f'''La persona que más habló fue {per_author.index[0]} con {per_author[0]} mensajes enviados en total''')
                st.write(f'''La persona que menos mensajes envió fue {per_author.index[-1]} con {per_author[-1]} en total.''')

            st.plotly_chart(msg_day_author_plot, use_container_width=True)
            
            
        with st.beta_expander('Por Tiempo'): 
            col3,col4 = st.beta_columns(2)
            with col3:
                st.plotly_chart(hours,use_container_width=True)
            with col4:
                st.plotly_chart(days_week,use_container_width=True)
            st.plotly_chart(calendar, use_container_width=True)
            
        with st.beta_expander('Por Palabras'):
            st.write(f'''El promedio de palabras por mensaje en esta conversación fue de {float(lenght.mean()):.2f}''')
            for i in range(1, len(lenght_author.columns)):
                st.write(f'''Promedio de cantidad de palabras utilizadas por mensaje de {lenght_author.columns[i]} es {float(lenght_author.iloc[0:,i].mean()):.2f}''')
            st.plotly_chart(lenght_plot, use_container_width=True)
            random8,random9,random10 = st.beta_columns(3)
            with random9:
                st.write('Nube de las 200 palabras más Utilizadas')
            st.pyplot(wc_plot)
            
        with st.beta_expander('Emojis'):    
            col5, col6 = st.beta_columns(2)
            with col5:    
                st.write('Los 15 Emojis más Usados en la Conversación \n')

                for key,value in emoji_dict[0:15]:
                    st.write(key ,'->' ,value)

            with col6:
                for i in authors:
                    dummy_df = df[df['Author'] == i]
                    total_emojis_list = list([a for b in dummy_df.emoji for a in b])
                    emoji_dict = dict(collections.Counter(total_emojis_list))
                    emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)
                    author_emoji_df = pd.DataFrame(emoji_dict[0:10], columns=['emoji', 'count'])
                    emoji_author = px.pie(author_emoji_df, values='count', names='emoji', title = 'Top 10 Emoji más Usados por ' + i, color_discrete_sequence=px.colors.qualitative.Antique)
                    emoji_author.update_traces(textposition='inside', textinfo='percent+label')   
                    st.plotly_chart(emoji_author)
