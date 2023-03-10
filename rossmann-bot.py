import pandas as pd
import json
import requests
import os
from flask import Flask,request,Response

#constants
TOKEN='6044419406:AAEZxSHwiV7bmNW5X7mpGTYpb6mQiB46JHA'
#chat_id='6054924276'

#Info about the Bot
#http://api.telegram.org/bot6044419406:AAEZxSHwiV7bmNW5X7mpGTYpb6mQiB46JHA/getMe

#get updates
#http://api.telegram.org/bot6044419406:AAEZxSHwiV7bmNW5X7mpGTYpb6mQiB46JHA/getUpdates

#webhook importante deletar e criar um novo com endereço do deploy
#http://api.telegram.org/bot6044419406:AAEZxSHwiV7bmNW5X7mpGTYpb6mQiB46JHA/deleteWebhook?
#http://api.telegram.org/bot6044419406:AAEZxSHwiV7bmNW5X7mpGTYpb6mQiB46JHA/setWebhook?url=https://rossmann-bot-y16i.onrender.com


#send message
#http://api.telegram.org/bot6044419406:AAEZxSHwiV7bmNW5X7mpGTYpb6mQiB46JHA/sendMessage?chat_id=6054924276&text=Hi Cida, I am doing well,tks!


def send_message(chat_id,text):
    url=f'https://api.telegram.org/bot{TOKEN}/'
    url=url +f"sendMessage?chat_id={chat_id}"
    #url='https://api.telegram.org/bot6044419406:AAEZxSHwiV7bmNW5X7mpGTYpb6mQiB46JHA/sendMessage?chat_id=6054924276'
    r=requests.post(url,json={'text':text})
    print(f'Status Code {r.status_code}')

    return None

def load_dataset(store_id):
    # loading test dataset
    df10 = pd.read_csv( 'test.csv' )
    df_store_raw = pd.read_csv( 'store.csv' )

    # merge test dataset + store
    df_test = pd.merge( df10, df_store_raw, how='left', on='Store' )

    # choose store for prediction
    #df_test = df_test[df_test['Store'].isin( [80, 95, 103] )]
    df_test = df_test[df_test['Store']==store_id]

    if not df_test.empty:
        # remove closed days
        df_test = df_test[df_test['Open'] == 1]
        #df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop( 'Id', axis=1 )

        # convert Dataframe to json
        data=json.dumps(df_test.to_dict(orient='records'))
    else:
        data='error'

    return data

def predict(data):
    # API call
    url='https://regression-rossmann.onrender.com/rossmann/predict'
    header={'content-type':'application/json'}
    data=data

    r=requests.post(url,data=data,headers=header)
    print(f'status code{r.status_code}')
    d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys() )
    return d1


def parse_message(message):
    chat_id=message['message']['chat']['id']
    store_id=message['message']['text']
    store_id=store_id.replace('/','')

    try:
        store_id= int(store_id)

    except ValueError:
        store_id='error'
    return chat_id,store_id


# api initialize

app= Flask(__name__)

@app.route('/',methods=['GET','POST'])



def index():
    if request.method=='POST':
        message=request.get_json()
        chat_id,store_id=parse_message(message)
        if store_id != 'error':
            # loading data
            data=load_dataset(store_id)

            if data !='error':
                # prediction
                d1=predict(data)

                # calculation
                d2 = d1[['store', 'prediction']].groupby( 'store' ).sum().reset_index()

                # send message
                msg='Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(d2[ 'store'].values[0], d2['prediction'].values[0])

                send_message(chat_id,msg)
                return Response('ok',status=200)
            else:
                send_message(chat_id,'Store Not Available')
                return Response('ok',status=200)
        else:
            send_message(chat_id,'Store ID is wrong')
            return Response('ok',status=200)
    else:
        return '<h1> RossmannTelegram BOT </h1>'
    
if __name__=='__main__':
    port=os.environ.get('PORT',5000)
    app.run(host='0.0.0.0',port=port)
  

