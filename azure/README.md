# Azure (не развёртывается автоматически)

`func start` локально поднимает HTTP-trigger `/api/analyze`; endpoint защищён function key в Azure (`auth_level=function`). `az deployment group create --resource-group <rg> --template-file azure/main.bicep` создаёт Storage Account и Consumption Function App. Удаление: `az group delete --name <rg>`.

Потенциально платные ресурсы: Function Consumption, Storage, исходящие запросы и OpenAI API. В репозитории не выполняются deployment и платные вызовы. Непроверено облаком: права, публикация кода, function key и Blob RBAC; локально проверяется только импорт/контракт при установленных Azure-пакетах.

Скрипты `scripts/azure_prepare.sh`, `scripts/azure_deploy.sh` и `scripts/azure_delete.sh` требуют ручного задания группы ресурсов. Deployment script намеренно не запускается автоматически; deletion необратим.

Схема Python v2-декоратора и `AuthLevel.FUNCTION` сверена с [официальной документацией Azure HTTP trigger](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger?tabs=python-v2%2Cin-process%2Cfunctionsv2).
