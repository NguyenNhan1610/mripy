class recon:
    def __initial__( self ):
        self.reglarization = []
        self.Nreg = 0
        

    def add_reglarization( self, reglarization ):
        self.Nreg = self.Nreg + 1
        self.reglarization.append(reglarization)
        
    def ADMM( self, param )
        pass

    #def CG( self, param )
        #pass