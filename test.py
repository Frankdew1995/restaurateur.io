from cloudprinting import list_jobs, submit_job, OAuth2

access_token="ya29.GlxXB0WFirzv8WPXOHlDIzYAUM1k4MXhDQm6-wq6m4FRYVudxnvXe79ePIdM-1FHiVeTR7vtiuc60--D2gRKACHPxRnBL845Uni_betGUzaTAIZk5QqiHbFmFOYu3Q"



auth = OAuth2(access_token=access_token,
              token_type="Bearer")


r = list_jobs(auth=auth)


s = submit_job(printer="3ab3234a-9392-c9bb-b787-47a8995392b9",
           content="Haijun_Du_CV_ZH.pdf",
           auth=auth)

print(s)






