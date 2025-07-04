import os
import json
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Google Sheets imports
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

load_dotenv()

class DataStorage:
    def __init__(self, storage_type: str = 'json'):
        self.storage_type = storage_type
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        
        if storage_type == 'gsheets' and GSHEETS_AVAILABLE:
            self._init_gsheets()
    
    def _init_gsheets(self):
        creds_file = os.getenv('GSHEETS_CREDENTIALS_FILE')
        if not creds_file:
            raise ValueError("Google Sheets credentials file not configured")
            
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open("DatingMatchmakerUsers").sheet1
    
    def _get_json_path(self):
        return self.data_dir / 'users.json'
    
    def _get_csv_path(self):
        return self.data_dir / 'users.csv'
    
    def create_user(self, user_data: dict) -> dict:
        if self.storage_type == 'json':
            return self._create_user_json(user_data)
        elif self.storage_type == 'csv':
            return self._create_user_csv(user_data)
        elif self.storage_type == 'gsheets':
            return self._create_user_gsheets(user_data)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def get_user(self, user_id: str) -> Optional[dict]:
        if self.storage_type == 'json':
            return self._get_user_json(user_id)
        elif self.storage_type == 'csv':
            return self._get_user_csv(user_id)
        elif self.storage_type == 'gsheets':
            return self._get_user_gsheets(user_id)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def get_all_users(self) -> List[dict]:
        if self.storage_type == 'json':
            return self._get_all_users_json()
        elif self.storage_type == 'csv':
            return self._get_all_users_csv()
        elif self.storage_type == 'gsheets':
            return self._get_all_users_gsheets()
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    # JSON implementations
    def _create_user_json(self, user_data: dict) -> dict:
        path = self._get_json_path()
        users = []
        
        if path.exists():
            with open(path, 'r') as f:
                users = json.load(f)
        
        user_id = str(len(users) + 1)
        user_data['id'] = user_id
        users.append(user_data)
        
        with open(path, 'w') as f:
            json.dump(users, f)
        
        return user_data
    
    def _get_user_json(self, user_id: str) -> Optional[dict]:
        path = self._get_json_path()
        if not path.exists():
            return None
            
        with open(path, 'r') as f:
            users = json.load(f)
        
        for user in users:
            if user.get('id') == user_id:
                return user
        return None
    
    def _get_all_users_json(self) -> List[dict]:
        path = self._get_json_path()
        if not path.exists():
            return []
            
        with open(path, 'r') as f:
            return json.load(f)
    
    # CSV implementations
    def _create_user_csv(self, user_data: dict) -> dict:
        path = self._get_csv_path()
        df = pd.DataFrame(columns=[
            'id', 'name', 'age', 'gender', 'bio', 
            'personality_traits', 'interests', 'values', 'looking_for'
        ])
        
        if path.exists():
            df = pd.read_csv(path)
        
        user_id = str(len(df) + 1)
        user_data['id'] = user_id
        # Convert lists to strings for CSV storage
        for field in ['personality_traits', 'interests', 'values']:
            user_data[field] = json.dumps(user_data.get(field, []))
        
        new_row = pd.DataFrame([user_data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(path, index=False)
        
        return user_data
    
    def _get_user_csv(self, user_id: str) -> Optional[dict]:
        path = self._get_csv_path()
        if not path.exists():
            return None
            
        df = pd.read_csv(path)
        user = df[df['id'] == user_id].to_dict('records')
        if not user:
            return None
        
        user = user[0]
        # Convert stringified lists back to lists
        for field in ['personality_traits', 'interests', 'values']:
            user[field] = json.loads(user[field])
        
        return user
    
    def _get_all_users_csv(self) -> List[dict]:
        path = self._get_csv_path()
        if not path.exists():
            return []
            
        df = pd.read_csv(path)
        users = df.to_dict('records')
        
        # Convert stringified lists back to lists
        for user in users:
            for field in ['personality_traits', 'interests', 'values']:
                user[field] = json.loads(user[field])
        
        return users
    
    # Google Sheets implementations
    def _create_user_gsheets(self, user_data: dict) -> dict:
        user_id = str(len(self.sheet.get_all_records()) + 1)
        user_data['id'] = user_id
        
        # Prepare data for Google Sheets
        row = [
            user_id,
            user_data.get('name', ''),
            user_data.get('age', ''),
            user_data.get('gender', ''),
            user_data.get('bio', ''),
            json.dumps(user_data.get('personality_traits', [])),
            json.dumps(user_data.get('interests', [])),
            json.dumps(user_data.get('values', [])),
            user_data.get('looking_for', '')
        ]
        
        self.sheet.append_row(row)
        return user_data
    
    def _get_user_gsheets(self, user_id: str) -> Optional[dict]:
        records = self.sheet.get_all_records()
        for record in records:
            if record.get('id') == user_id:
                # Convert stringified lists back to lists
                for field in ['personality_traits', 'interests', 'values']:
                    record[field] = json.loads(record[field])
                return record
        return None
    
    def _get_all_users_gsheets(self) -> List[dict]:
        records = self.sheet.get_all_records()
        for record in records:
            for field in ['personality_traits', 'interests', 'values']:
                record[field] = json.loads(record[field])
        return records