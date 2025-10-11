"""
微信支付工具类
"""
import os
import time
import hashlib
import hmac
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
import xmltodict


class WeChatPay:
    """微信支付工具类"""
    
    def __init__(self):
        # 微信支付配置
        self.app_id = "your_app_id"  # 微信小程序AppID
        self.mch_id = "your_mch_id"  # 商户号
        self.api_key = "your_api_key"  # API密钥
        self.notify_url = "https://your-domain.com/api/payment/notify"  # 支付回调地址
        
        # 证书路径
        self.cert_path = "certs/apiclient_cert.pem"
        self.key_path = "certs/apiclient_key.pem"
        
        # API地址
        self.unified_order_url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
        self.query_order_url = "https://api.mch.weixin.qq.com/pay/orderquery"
        
    def create_order(self, openid: str, service_type: str, description: str) -> Dict[str, Any]:
        """
        创建支付订单
        
        Args:
            openid: 用户openid
            service_type: 服务类型 (report, medication, education, dermatology)
            description: 订单描述
            
        Returns:
            支付参数
        """
        try:
            # 生成订单号
            out_trade_no = f"{service_type}_{int(time.time())}_{openid[-8:]}"
            
            # 订单金额（分）
            total_fee = 990  # 9.9元 = 990分
            
            # 构建支付参数
            params = {
                'appid': self.app_id,
                'mch_id': self.mch_id,
                'nonce_str': self._generate_nonce_str(),
                'body': description,
                'out_trade_no': out_trade_no,
                'total_fee': total_fee,
                'spbill_create_ip': '127.0.0.1',
                'notify_url': self.notify_url,
                'trade_type': 'JSAPI',
                'openid': openid
            }
            
            # 生成签名
            params['sign'] = self._generate_sign(params)
            
            # 转换为XML
            xml_data = self._dict_to_xml(params)
            
            # 发送请求
            response = requests.post(
                self.unified_order_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = self._xml_to_dict(response.text)
                
                if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
                    # 生成小程序支付参数
                    prepay_id = result['prepay_id']
                    pay_params = self._generate_miniprogram_pay_params(prepay_id)
                    
                    return {
                        'success': True,
                        'data': {
                            'out_trade_no': out_trade_no,
                            'prepay_id': prepay_id,
                            'pay_params': pay_params
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('err_code_des', '支付订单创建失败')
                    }
            else:
                return {
                    'success': False,
                    'message': f'请求失败: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'创建订单异常: {str(e)}'
            }
    
    def query_order(self, out_trade_no: str) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            out_trade_no: 商户订单号
            
        Returns:
            订单状态信息
        """
        try:
            params = {
                'appid': self.app_id,
                'mch_id': self.mch_id,
                'out_trade_no': out_trade_no,
                'nonce_str': self._generate_nonce_str()
            }
            
            params['sign'] = self._generate_sign(params)
            xml_data = self._dict_to_xml(params)
            
            response = requests.post(
                self.query_order_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = self._xml_to_dict(response.text)
                
                if result.get('return_code') == 'SUCCESS':
                    return {
                        'success': True,
                        'data': {
                            'trade_state': result.get('trade_state'),
                            'transaction_id': result.get('transaction_id'),
                            'total_fee': result.get('total_fee')
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('return_msg', '查询失败')
                    }
            else:
                return {
                    'success': False,
                    'message': f'请求失败: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'查询订单异常: {str(e)}'
            }
    
    def verify_notify(self, xml_data: str) -> Dict[str, Any]:
        """
        验证支付回调
        
        Args:
            xml_data: 回调XML数据
            
        Returns:
            验证结果
        """
        try:
            result = self._xml_to_dict(xml_data)
            
            # 验证签名
            if self._verify_sign(result):
                return {
                    'success': True,
                    'data': {
                        'out_trade_no': result.get('out_trade_no'),
                        'transaction_id': result.get('transaction_id'),
                        'total_fee': result.get('total_fee'),
                        'trade_state': result.get('trade_state')
                    }
                }
            else:
                return {
                    'success': False,
                    'message': '签名验证失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'验证回调异常: {str(e)}'
            }
    
    def _generate_nonce_str(self) -> str:
        """生成随机字符串"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        # 过滤空值并排序
        filtered_params = {k: v for k, v in params.items() if v and k != 'sign'}
        sorted_params = sorted(filtered_params.items())
        
        # 拼接字符串
        string_a = '&'.join([f'{k}={v}' for k, v in sorted_params])
        string_sign_temp = f'{string_a}&key={self.api_key}'
        
        # MD5签名
        return hashlib.md5(string_sign_temp.encode('utf-8')).hexdigest().upper()
    
    def _verify_sign(self, params: Dict[str, Any]) -> bool:
        """验证签名"""
        sign = params.pop('sign', '')
        calculated_sign = self._generate_sign(params)
        return sign == calculated_sign
    
    def _dict_to_xml(self, params: Dict[str, Any]) -> str:
        """字典转XML"""
        xml = '<xml>'
        for k, v in params.items():
            xml += f'<{k}><![CDATA[{v}]]></{k}>'
        xml += '</xml>'
        return xml
    
    def _xml_to_dict(self, xml_str: str) -> Dict[str, Any]:
        """XML转字典"""
        try:
            return xmltodict.parse(xml_str)['xml']
        except:
            # 备用解析方法
            root = ET.fromstring(xml_str)
            result = {}
            for child in root:
                result[child.tag] = child.text
            return result
    
    def _generate_miniprogram_pay_params(self, prepay_id: str) -> Dict[str, str]:
        """生成小程序支付参数"""
        params = {
            'appId': self.app_id,
            'timeStamp': str(int(time.time())),
            'nonceStr': self._generate_nonce_str(),
            'package': f'prepay_id={prepay_id}',
            'signType': 'MD5'
        }
        
        # 生成paySign
        params['paySign'] = self._generate_sign(params)
        
        return params


# 支付服务类型映射
PAYMENT_SERVICES = {
    'report': {
        'name': '报告解读',
        'description': '医学报告智能解读服务',
        'price': 9.9
    },
    'medication': {
        'name': '药物咨询',
        'description': '专业药物咨询指导服务',
        'price': 9.9
    },
    'education': {
        'name': '健康科普',
        'description': '权威健康知识科普服务',
        'price': 9.9
    },
    'dermatology': {
        'name': '皮肤病诊断',
        'description': '皮肤病智能诊断分析服务',
        'price': 9.9
    }
}

