# PCR_JJC_Notification
公主连结竞技场工具  

forked from https://github.com/ID44977/PCR_JJC_Notification

使用方法：  
1.创建secrets  
  单UID使用时设置名为 UID 的secret，值为13位数字ID。
  多UID使用时设置名为 UID_UNAME 的secret，值为你自己的公主连结id和昵称(自定义仅用于区分推送)，例如 `1111111111111 foo;2222222222222bar`
  企业微信设置名为 QYWX 的secret，值为 企业ID;应用ID;应用密钥，例如 `wws12je3d2d2pdh81h0;1000002;tVDVERV-0Dcwdncjuwexcnweuxboweu`
  申请企业微信推送通道仍可参照：https://sct.ftqq.com/forward ，由于配额限制，此脚本直接使用接口而不是用S酱转发。
  
2.运行actions中的run Query
  目前默认每天中午12点（GMT+8）运行  
