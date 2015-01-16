// example.cpp : Defines the entry point for the console application.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "DevoceControl.h"

int main(int argc, char* argv[])
{

  printf("Hello World!\n");
	
  int iRet = 0;	  
  
  unsigned char * pucInData = (unsigned char *)"¼×ÒÒ±ûABC123";
  unsigned int uiInDataLen = strlen((char *)pucInData );
	
  unsigned char *pszCert = (unsigned char *)"MIIBkjCCATigAwIBAgIDEX4lMAoGCCqBHM9VAYN1MDkxCzAJBgNVBAYTAkNOMSowKAYDVQQDDCHnp7vliqjkupLogZTnvZHlronlhajmnI3liqHlubPlj7AwHhcNMTQwNzA5MDYzMzQxWhcNMTUwNzA5MDYzMzQxWjA5MQswCQYDVQQGEwJDTjEqMCgGA1UEAwwhMjAxNDAzMjExMTM4MTMwMTIxNjg3QDE1MzIxOTc4Njg1MFkwEwYHKoZIzj0CAQYIKoEcz1UBgi0DQgAEPztLGItdSCbsQkBV3oimr7SqX0YSjio2UTQZHGqlTEisf+isJCnMy0WK2aTz9jJis3C3udInjlHMu16gwdha+6MvMC0wCwYDVR0PBAQDAgQwMBMGA1UdJQQMMAoGCCsGAQUFBwMBMAkGA1UdEwQCMAAwCgYIKoEcz1UBg3UDSAAwRQIgWq7m6DzoawiTilPqVWZipU86bwSqRAgJgyenesajcmsCIQC+omRTM1oyVvV2ACqdWUtO6Vg2Gts85VvSM0O8Xg/N0g==";
  unsigned int uiPszCertLen = strlen((char *)pszCert);
  
  unsigned char enceData[400] = {0};
  unsigned long ulEncedData = 0; 
  
  unsigned char OutData[400] = {0};
  unsigned long ulOutData = 0;
  
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
  printf("instructCrpRequest begin----------------------------------------------\n");
  iRet =  instructCrpRequest(pucInData, uiInDataLen , pszCert, uiPszCertLen, 5, OutData, (unsigned int *)&ulOutData );
  if(iRet == 0)
  {
     printf("instructCrpRequest successs, outdata:%s\n", OutData);
  }
  else
  {
     printf("instructCrpRequest error with code:%d\n" ,iRet );
     return iRet;
  } 
	printf("FinalizeDeviceControlInterface begin----------------------------------------------\n");
  iRet = FinalizeDeviceControlInterface();
  if(iRet == 0)
  {
     printf("FinalizeDeviceControlInterface successs\n");
  }
  else
  {
     printf("FinalizeDeviceControlInterface error with code:%d\n" ,iRet );
     return iRet;
  }
  
  return iRet;
}

