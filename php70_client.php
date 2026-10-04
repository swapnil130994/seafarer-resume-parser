<?php
function parseSeafarerResume($filePath, $apiUrl)
{
    if (!file_exists($filePath)) return array('success'=>false,'error'=>'Resume file not found.');
    if (!function_exists('curl_init')) return array('success'=>false,'error'=>'PHP cURL extension is not enabled.');
    $mime='application/octet-stream';
    if (function_exists('mime_content_type')) { $detected=@mime_content_type($filePath); if($detected)$mime=$detected; }
    $file=new CURLFile($filePath,$mime,basename($filePath));
    $ch=curl_init($apiUrl);
    curl_setopt($ch,CURLOPT_POST,true); curl_setopt($ch,CURLOPT_POSTFIELDS,array('file'=>$file));
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,true); curl_setopt($ch,CURLOPT_CONNECTTIMEOUT,20); curl_setopt($ch,CURLOPT_TIMEOUT,180);
    curl_setopt($ch,CURLOPT_HTTPHEADER,array('Accept: application/json'));
    $response=curl_exec($ch); $err=curl_error($ch); $code=curl_getinfo($ch,CURLINFO_HTTP_CODE); curl_close($ch);
    if($response===false||$err)return array('success'=>false,'error'=>$err);
    $json=json_decode($response,true);
    if($code<200||$code>=300)return array('success'=>false,'http_code'=>$code,'error'=>isset($json['detail'])?$json['detail']:$response);
    return array('success'=>true,'http_code'=>$code,'data'=>$json);
}
