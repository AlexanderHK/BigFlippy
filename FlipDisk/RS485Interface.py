# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:18:35 2024

@author: bigfl
"""
import numpy as np
import serial
import gpiod
from gpiod.line import Direction, Value
import PixelBoard as PB




  
    
   
 

class RS485Interface:

    def __init__(self):
        self.EN_485 =  4
        gpiod.is_gpiochip_device("/dev/gpiochip4")
        self.request = gpiod.request_lines(
             "/dev/gpiochip4",
             consumer="blink-example",
             config={
                 self.EN_485: gpiod.LineSettings(
                     direction=Direction.OUTPUT, output_value=Value.ACTIVE
                 )
             },
        )
        self.t = serial.Serial("/dev/ttyAMA0",19200)
        print (self.t.portstr)
    
    def binary_to_hex_byte(self, binary_str):

        """Convert an 8-bit binary string to a bytes object."""
        if len(binary_str) != 8 or not all(bit in '01' for bit in binary_str):
            raise ValueError("Input must be an 8-bit binary string")
        #print(bytes([int(binary_str, 2)]))
        return bytes([int(binary_str, 2)]) 

    def getSerial(self,vBoard, command):
        serialArr=list()
        for x in range(0, vBoard.PANEL_NUM):
            serialArr.append(b'\x80') 
        match command:
        
            #send update to all panels to refresh
            case 1:
                serialArr=list()
                serialArr.append(b'\x80\x82\x8F')
                return serialArr
             
            # update panel values but dont refresh
            case 2:
                for x in range(0, vBoard.PANEL_NUM):
                    serialArr[x]+=b'\x83'
                    serialArr[x]+=(vBoard.PANEL_NUM-x).to_bytes(1, byteorder='big')
                    
                    
            #update panel values and refresh immediately
            case 3:
                for x in range(0, vBoard.PANEL_NUM):
                    serialArr[x]+=b'\x84'
            case _:
                print("invalid command")
                
        for y in range(0, len(serialArr)):
            binString=''
            for i in range(0,28):
                binString = '0'+str(vBoard.board[i,y*7+0])+str(vBoard.board[i,y*7+1])+str(vBoard.board[i,y*7+2])+str(vBoard.board[i,y*7+3])+str(vBoard.board[i,y*7+4])+str(vBoard.board[i,y*7+5])+str(vBoard.board[i,y*7+6])
                serialArr[y]+=self.binary_to_hex_byte(binString)
            serialArr[y]+=b'\x8F'
        return serialArr
    
    def sendMessage(self, byteArr):
        for x in range(0, len(byteArr)):
           self.t.write(byteArr[x])
    def Close(self):
        self.t.close()
