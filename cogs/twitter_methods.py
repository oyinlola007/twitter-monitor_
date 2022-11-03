import requests, os, urllib, math, asyncio

import cogs.config as config
import cogs.db as db

def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(config.BEARER_TOKEN)}
    return headers

def connect_to_endpoint(url, headers, params, pagination_token = None):
    params['pagination_token'] = pagination_token   #params object received from create_url function
    response = requests.request("GET", url, headers = headers, params = params)
    #print("Endpoint Response Code: " + str(response.status_code))
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    if response.status_code == 429:
        print("Limit reached, will try again in 30 seconds")
    return response.json()

def create_url(id):
    search_url = f"https://api.twitter.com/2/users/{id}/following" #Change to the endpoint you want to collect data from

    #change params based on the endpoint you are using
    query_params = {'max_results': 1000,
                    'pagination_token': {}}
    return (search_url, query_params)

async def get_id(user_name):
    flag = True
    headers = create_headers(config.BEARER_TOKEN)

    while flag:
        url = f"https://api.twitter.com/2/users/by?usernames={user_name}&user.fields=id"
        response = requests.request("GET", url, headers = headers)
        print("Endpoint Response Code: " + str(response.status_code))
        if response.status_code == 429:
            #raise Exception(response.status_code, response.text)
            print("Limit reached, will try again in 30 seconds")
            await asyncio.sleep(30)
            continue

        return response.json()['data'][0]['id']


async def get_following(id):
    flag = True
    next_token = None
    headers = create_headers(config.BEARER_TOKEN)
    result = []

    while flag:
        url = create_url(id)
        try:
            json_response = connect_to_endpoint(url[0], headers, url[1], next_token)
            result_count = json_response['meta']['result_count']

            if 'next_token' in json_response['meta']:
                # Save the token to use for next call
                next_token = json_response['meta']['next_token']
                print("Pagination Token: ", next_token)
                if result_count is not None and result_count > 0 and next_token is not None:
                    for data in json_response['data']:
                        result.append([data['id'], data['name'], data['username']])
                    await asyncio.sleep(5)
            # If no pagination_token exists
            else:
                if result_count is not None and result_count > 0:
                    for data in json_response['data']:
                        result.append([data['id'], data['name'], data['username']])
                    await asyncio.sleep(5)

                #Since this is the final request, turn flag to false to move to the next time period.
                flag = False
                next_token = None
        except:
            await asyncio.sleep(5)
            pass

        await asyncio.sleep(5)

    return result


def ragged_chunks(seq, chunks):
    size = len(seq)
    start = 0
    for i in range(size, size * chunks + 1, size):
        stop = i // chunks
        yield seq[start:stop]
        start = stop

def de_join(data):
    chunks = math.ceil(len(data)/1900)
    list_ = data.split(",")
    list_ = ragged_chunks(list_, chunks)
    list_ = [",".join(l) for l in list_]
    return list_

