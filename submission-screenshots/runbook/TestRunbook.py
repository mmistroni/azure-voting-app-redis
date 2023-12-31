#!/usr/bin/env python3
print('Executing my first runbook')
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

SUBSCRIPTION_ID="37667572-c49c-408d-9095-c966e587dc85"
RESOURCE_GROUP ='project3-rg'
MACHINE_NAME = 'UbuntuVM'


# Wrap credentials from azure-identity to be compatible with SDK that needs msrestazure or azure.common.credentials
# Need msrest >= 0.6.0
# See also https://pypi.org/project/azure-identity/

from msrest.authentication import BasicTokenAuthentication
from azure.core.pipeline.policies import BearerTokenCredentialPolicy
from azure.core.pipeline import PipelineRequest, PipelineContext
from azure.core.pipeline.transport import HttpRequest

from azure.identity import DefaultAzureCredential

class CredentialWrapper(BasicTokenAuthentication):
    def __init__(self, credential=None, resource_id="https://management.azure.com/.default", **kwargs):
        """Wrap any azure-identity credential to work with SDK that needs azure.common.credentials/msrestazure.
        Default resource is ARM (syntax of endpoint v2)
        :param credential: Any azure-identity credential (DefaultAzureCredential by default)
        :param str resource_id: The scope to use to get the token (default ARM)
        """
        super(CredentialWrapper, self).__init__(None)
        if credential is None:
            credential = DefaultAzureCredential()
        self._policy = BearerTokenCredentialPolicy(credential, resource_id, **kwargs)

    def _make_request(self):
        return PipelineRequest(
            HttpRequest(
                "CredentialWrapper",
                "https://fakeurl"
            ),
            PipelineContext(None)
        )

    def set_token(self):
        """Ask the azure-core BearerTokenCredentialPolicy policy to get a token.
        Using the policy gives us for free the caching system of azure-core.
        We could make this code simpler by using private method, but by definition
        I can't assure they will be there forever, so mocking a fake call to the policy
        to extract the token, using 100% public API."""
        request = self._make_request()
        self._policy.on_request(request)
        # Read Authorization, and get the second part after Bearer
        token = request.http_request.headers["Authorization"].split(" ", 1)[1]
        self.token = {"access_token": token}

    def signed_session(self, session=None):
        self.set_token()
        return super(CredentialWrapper, self).signed_session(session)






azure_credential = CredentialWrapper()


print('Initialize client.....')
# Initialize client with the credential and subscription.
compute_client = ComputeManagementClient(
    azure_credential,
    SUBSCRIPTION_ID
)

print('\nUpdating VMSS capcity')

myvmss = compute_client.virtual_machine_scale_sets.get("udacity-rg", "udacity-vmss")
print("Initial myvmss.sku.capacity = ",myvmss.sku.capacity)
myvmss.sku.capacity = 4
print("New myvmss.sku.capacity = ",myvmss.sku.capacity)
# Increase the VMSS SKU Capacity
async_vmss = compute_client.virtual_machine_scale_sets.create_or_update("udacity-rg", "udacity-vmss", myvmss)
async_vmss.wait()



print('\nFinished updating capacity.')



