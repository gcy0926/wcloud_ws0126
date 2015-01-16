// example.cpp : Defines the entry point for the console application.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "DevoceControl.h"

unsigned char* Encry(unsigned char * pucInData, unsigned int uiInDataLen,unsigned char *pszCert,unsigned int uiPszCertLen,unsigned char* OutData)
{

	
  int iRet = 0;	  
   
  unsigned long ulOutData = 0;
  
  iRet = InitDeviceControlInterface();
  printf("instructCrpRequest begin----------------------------------------------\n");
  iRet =  instructCrpRequest(pucInData, uiInDataLen , pszCert, uiPszCertLen, 5, OutData, (unsigned int *)&ulOutData );
  iRet = FinalizeDeviceControlInterface();
   printf("FinalizeDeviceControlInterface begin----------------------------------------------\n");
  return OutData;
}
