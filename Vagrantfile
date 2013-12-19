# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
        # Base box to build off, and download URL for when it doesn't exist
        # on the user's system already
        config.vm.box = "precise-server64"
        config.vm.box_url =
"http://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-amd64-vagrant-disk1.box"

	#config.vm.hostname = "kamudev"

        # Assign this VM to a host only network IP, allowing you to access
        # it
        # via the IP.
        config.vm.network "private_network", ip: "192.168.107.2"

        # Forward a port from the guest to the host, which allows for
        # outside
        # computers to access the VM, whereas host only networking does not.
        config.vm.network "forwarded_port", guest: 8000, host: 8107

        # Enable provisioning with a shell script.
        config.vm.provision "ansible" do |ansible|
		ansible.inventory_file = "provisioning/dev"
                ansible.playbook = "provisioning/playbook.yml"
        end
end
