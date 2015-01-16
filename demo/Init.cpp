// example.cpp : Defines the entry point for the console application.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "DevoceControl.h"

int main()
{
   int iRet = 0;
  printf("InitDeviceControlInterface begin------------------------------------\n");
  iRet = InitDeviceControlInterface();
  if(iRet == 0)
  {
     printf("InitDeviceControlInterface successs\n");
  }
  else
  {
     printf("InitDeviceControlInterface error with code:%d\n" ,iRet );
     return iRet;
  }
  return iRet;
}

