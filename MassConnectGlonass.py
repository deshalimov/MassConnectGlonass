from urllib.parse import quote
import requests
import json
import time
import random


environment = prod

class MassConnect:

    def __init__(self, login: str, password: str):
        self.refresh_token = self.get_access_token(login, password).json()['refresh_token']
        self.brands = self.getBrands()
            
    def set_object_monitoring(self, status, brandName, modelName, trackerNumber, trackerPhoneNumber, startDate, endDate, vehicleName, carrier):
        first_response = self.getVehiclesInfo(vehicleName, "")
        # если ТС с определенным номером найден один
        if len(first_response) == 1:
            response_get_vehicles_info = first_response
        else:
            #если ТС хуева гора, Уточняем кто ГП и отправляем запрос заново
            response_get_vehicles_info = self.getVehiclesInfo(vehicleName, "&carrier=" + str(self.get_id_carrier(carrier)))
        if len(response_get_vehicles_info) != 1:
            print (f"для Тс {vehicleName} {carrier} найдено {len(response_get_vehicles_info)}")
        else:
            vehicleId = response_get_vehicles_info[0]['id']
            carrierId = response_get_vehicles_info[0]['carrier']['id']

            
        
            access_token: str = self.refreshToken(self.refresh_token)
            url = f'https://{environment}/api/trackers/v1/trackers'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            data = {
                "provider": "glonass",
                "status": self.getStatus(status),
                "brandId": self.brands[brandName],
                "modelId": massConnect.getModels(self.brands[brandName], modelName),
                "trackerNumber": trackerNumber,
                "trackerPhoneNumber": trackerPhoneNumber,
                "startDate": startDate,
                "endDate": endDate,
                "carrierId": carrierId,
                "vehicleId": vehicleId
            }
            try:
                res = requests.post(url, headers=headers, data=json.dumps(data))
                if res.status_code != 201:
                    print(f"Не успешно, {vehicleName} {carrier}. Ошибка при отправке запроса. Код {res.status_code}. Ошибка: {res.text}" )
                print(f"Успешно, {vehicleName} {carrier}")
            except:
                print(f"Не успешно, {vehicleName} {carrier}. Ошибка отправки запроса. ")

    def set_object_monitoring_by_id(self, status, brandName, modelName, trackerNumber, trackerPhoneNumber, startDate, endDate, vehicleId, carrierId):
            #time.sleep(random.randint(1,10))
            access_token: str = self.refreshToken(self.refresh_token)
            url = f'https://{environment}/api/trackers/v1/trackers'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            data = {
                "provider": "glonass",
                "status": self.getStatus(status),
                "brandId": None, # self.brands[brandName],
                "modelId": None, # massConnect.getModels(self.brands[brandName], modelName),
                "trackerNumber": trackerNumber,
                "trackerPhoneNumber": trackerPhoneNumber,
                "startDate": startDate,
                "endDate": endDate,
                "carrierId": carrierId,
                "vehicleId": vehicleId
            }
            try:
                res = requests.post(url, headers=headers, data=json.dumps(data))
                if res.status_code != 201:
                    print(f"Ошибка при отправке запроса. v.id = {vehicleId}, Код {res.status_code}. Ошибка: {res.text}" )
                print(f"{res.status_code}, v.id = {vehicleId}")
            except:
                print(f"Ошибка отправки запроса. v.id = {vehicleId}")

    def get_access_token(self, login, password):
        uri = f'https://{environment}/jwt-auth/connect/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'password',
            'username': login,
            'password': password,
            'scope': 'eq-admin-panel offline_access',
        }
        try:
            resp =  requests.post(uri, headers=headers, data=data)
            if resp.status_code != 200:
                print(f"Ошибка при авторизации. Код {resp.status_code}. Ошибка: {resp.text}" )
            return resp
        except:
            print("Ошибка при авторизации")
        
    def refreshToken(self, refresh_token) -> str:
        uri = f'https://{environment}/jwt-auth/connect/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        try:
            resp =  requests.post(uri, headers=headers, data=data)
            if resp.status_code != 200:
                print(f"Ошибка при обновлении токена. Код {resp.status_code}. Ошибка: {resp.text}" )
            self.refresh_token = resp.json()['refresh_token']
            return resp.json()['access_token']
        except:
            print("Ошибка при обновлении токена")
    
    def getStatus(self, status):
        match status:
            case "Используется":
                return "active"
            case "Удален":
                return "deleted"
            case "Не подключен":
                return "notConnected"
    
    def getBrands(self):
        url = f'https://{environment}/api/trackers/v1/brands?page=1&per-page=1000'
        access_token = self.refreshToken(self.refresh_token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        fix = requests.get(url, headers=headers).json()['entities']
        brand_dict = dict()
        for item in fix:
            brand_dict.update({item['name']: item['id']})
        return brand_dict
    
    def getModels(self, brand_id, model_name):
        url = f'https://{environment}/api/trackers/v1/models?brandId={brand_id}&page=1&per-page=1000'
        access_token = self.refreshToken(self.refresh_token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        mod = requests.get(url, headers=headers).json()['entities']
        
        for item in mod:
            if item['name']==model_name:
                return (item['id'])
        print (f"Нет модели трекера {model_name} для выбранного трекера.")

    def getVehiclesInfo(self, vehicle_number, carrier):
        licence_plate = quote("*" + vehicle_number + "*")
        url = f'https://{environment}/api/native/v1.0/vehicles?page=1&per-page=20&order-by=id%7Cdesc&licensePlate={licence_plate}{carrier}'
        access_token = self.refreshToken(self.refresh_token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        return requests.get(url, headers=headers).json()['entities']
        
    def get_id_carrier(self, carrier):
        access_token = self.refreshToken(self.refresh_token)

        url = f'https://{environment}/api/native/v1.0/carriers?per-page=100&page=1&status%5B%5D=confirmed&status%5B%5D=not_confirmed&status%5B%5D=trial&status%5B%5D=confirmation_process&status%5B%5D=deleted&status%5B%5D=rejected&status%5B%5D=confirmation_process_with_eq&profileDetails%5BorganizationName%5D='
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(url + quote("*" + carrier + "*", encoding='utf-8'), headers=headers).json()
        if(response["total"] == 1):
            return response["entities"][0]["id"]
        else:
            return ""


    
if __name__ == '__main__':
    massConnect = MassConnect('login', 'password')
   